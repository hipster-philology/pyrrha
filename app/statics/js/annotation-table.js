/* Pyrrha annotation table — Vue 3 CDN, no build step */
(function () {
  'use strict';

  const { createApp, ref, reactive, computed, watch, nextTick, onMounted, onBeforeUnmount } = Vue;

  function csrfHeaders() {
    const token = document.querySelector('meta[name="csrf-token"]')?.content;
    return token ? { 'X-CSRFToken': token } : {};
  }

  // ── Allowed-list cache (session, 1 h TTL, 300 entries per category) ─────────
  const CACHE_TTL  = 60 * 60 * 1000;
  const CACHE_MAX  = 300;
  const _allowedCache = { lemma: new Map(), POS: new Map(), morph: new Map(), default: new Map() };

  function cachedAllowed(baseUrl, type, query) {
    const store    = _allowedCache[type] ?? _allowedCache.default;
    const now      = Date.now();
    const cacheKey = `${baseUrl}\x00${query}`;
    const entry    = store.get(cacheKey);
    if (entry && now - entry.ts < CACHE_TTL) {
      // Move to end of Map so LRU eviction keeps frequently-used entries alive
      store.delete(cacheKey);
      store.set(cacheKey, entry);
      return entry.promise;
    }
    if (store.size >= CACHE_MAX) store.delete(store.keys().next().value);
    const promise = fetch(baseUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...csrfHeaders() },
      body: JSON.stringify({ form: query }),
    }).then(r => r.json()).then(d => Array.isArray(d) ? d : []).catch(() => []);
    store.set(cacheKey, { promise, ts: now });
    return promise;
  }

  // ── Autocomplete fetch ───────────────────────────────────────────────────────

  async function fetchSuggestions(urls, type, query) {
    if (!urls) return [];
    const q        = (query || '').toLowerCase();
    const postOpts = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...csrfHeaders() },
      body: JSON.stringify({ form: q }),
    };
    const safeJson = p => p.then(r => r.json()).then(d => Array.isArray(d) ? d : []).catch(() => []);
    const [allowed, custom] = await Promise.all([
      urls.allowed ? cachedAllowed(urls.allowed, type, q) : Promise.resolve([]),
      urls.custom  ? safeJson(fetch(urls.custom, postOpts))  : Promise.resolve([]),
    ]);
    // Normalize to {value, label} regardless of API shape (plain string or object)
    const normalize = item => {
      if (!item) return null;
      return typeof item === 'string'
        ? { value: item, label: item }
        : { value: item.value, label: item.label || item.value };
    };
    const merged = [...allowed, ...custom].map(normalize).filter(Boolean);
    const seen = new Set();
    return merged.filter(item => {
      if (seen.has(item.value)) return false;
      seen.add(item.value); return true;
    }).sort((a, b) => a.value.localeCompare(b.value));
  }

  // ── AnnotationField ──────────────────────────────────────────────────────────

  const AnnotationField = {
    name: 'AnnotationField',
    props: {
      label: String,
      fieldKey: String,
      modelValue: { type: String, default: '' },
      savedValue: { type: String, default: '' },
      autocompleteUrls: Object,
      fieldType: { type: String, default: 'text' },
      invalid: { type: Boolean, default: false },
      customDictUrl: String,
    },
    emits: ['update:modelValue', 'dict-added', 'tab-next', 'tab-prev', 'save'],
    setup(props, { emit, expose }) {
      const open         = ref(false);
      const query        = ref('');
      const suggestions  = ref([]);
      const loading      = ref(false);
      const activeIndex  = ref(-1);
      const addingToDict = ref(false);
      const addedToDict  = ref(false);
      const root         = ref(null);
      const inputRef     = ref(null);   // single input for dropdown fields
      const glossRef     = ref(null);
      const ddListRef    = ref(null);
      let debounce = null;

      // Close when clicking outside — commit any typed query first so Save button click doesn't lose it
      function onDocClick(e) {
        if (root.value && !root.value.contains(e.target)) {
          if (open.value && query.value.trim()) emit('update:modelValue', query.value.trim());
          close();
        }
      }
      onMounted(() => document.addEventListener('mousedown', onDocClick));
      onBeforeUnmount(() => document.removeEventListener('mousedown', onDocClick));

      function close() {
        open.value = false;
        activeIndex.value = -1;
        query.value = '';
      }

      // Exposed: lets TokenRow focus this field via Tab navigation
      function focus() {
        nextTick(() => {
          if (props.autocompleteUrls) inputRef.value?.focus();
          else glossRef.value?.focus();
        });
      }

      // Commit any typed query to model value — called by TokenRow before saving
      function flush() {
        if (open.value && query.value.trim()) {
          emit('update:modelValue', query.value.trim());
        }
      }

      expose({ focus, flush });

      // Called when the autocomplete input receives focus
      function onInputFocus() {
        open.value = true;
        query.value = props.modelValue ?? '';
        activeIndex.value = -1;
        suggestions.value = [];
        if (props.autocompleteUrls) {
          loading.value = true;
          fetchSuggestions(props.autocompleteUrls, props.fieldType, query.value).then(s => {
            suggestions.value = s;
            loading.value = false;
          });
        }
      }

      function onQueryInput(e) {
        if (!open.value) {
          // Field was closed (e.g. after Ctrl+Enter): start fresh from the typed character only
          open.value = true;
          query.value = e.data ?? '';
          activeIndex.value = -1;
          suggestions.value = [];
        } else {
          query.value = e.target.value;
          activeIndex.value = -1;
        }
        if (!props.autocompleteUrls) return;
        clearTimeout(debounce);
        debounce = setTimeout(() => {
          loading.value = true;
          fetchSuggestions(props.autocompleteUrls, props.fieldType, query.value).then(s => {
            suggestions.value = s;
            loading.value = false;
          });
        }, 180);
      }

      function itemCount() {
        return filteredSuggestions.value.length + (hasCustomEntry.value ? 1 : 0);
      }

      function scrollActiveIntoView() {
        if (!ddListRef.value) return;
        const items = ddListRef.value.querySelectorAll('.dd-item');
        items[activeIndex.value]?.scrollIntoView({ block: 'nearest' });
      }

      function onInputKeydown(e) {
        if (e.ctrlKey && e.key === 'Enter') {
          e.preventDefault();
          if (query.value.trim()) emit('update:modelValue', query.value.trim());
          close();
          emit('save');
          return;
        }
        if (e.key === 'Tab') {
          e.preventDefault();
          if (query.value.trim()) emit('update:modelValue', query.value.trim());
          close();
          if (e.shiftKey) emit('tab-prev', props.fieldKey);
          else            emit('tab-next', props.fieldKey);
          return;
        }
        if (e.key === 'Escape') { e.preventDefault(); close(); return; }
        if (!open.value) return;
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          activeIndex.value = Math.min(activeIndex.value + 1, itemCount() - 1);
          nextTick(scrollActiveIntoView);
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          activeIndex.value = Math.max(activeIndex.value - 1, -1);
          nextTick(scrollActiveIntoView);
        } else if (e.key === 'Enter') {
          e.preventDefault();
          if (activeIndex.value >= 0 && activeIndex.value < filteredSuggestions.value.length) {
            pick(filteredSuggestions.value[activeIndex.value]);
          } else if (activeIndex.value === filteredSuggestions.value.length && hasCustomEntry.value) {
            pickCustom();
          } else if (query.value.trim()) {
            pickCustom();
          }
        }
      }

      function onGlossKeydown(e) {
        if (e.ctrlKey && e.key === 'Enter') {
          e.preventDefault();
          emit('save');
        } else if (e.key === 'Tab') {
          e.preventDefault();
          if (e.shiftKey) emit('tab-prev', props.fieldKey);
          else            emit('tab-next', props.fieldKey);
        }
      }

      function pick(item) {
        emit('update:modelValue', item.value);
        close();
      }

      function pickCustom() {
        if (query.value.trim()) {
          emit('update:modelValue', query.value.trim());
          close();
        }
      }

      async function addToDict() {
        if (!props.customDictUrl || !props.modelValue) return;
        addingToDict.value = true;
        try {
          const body = new FormData();
          body.append('value', props.modelValue);
          body.append('category', props.fieldKey || props.label);
          const resp = await fetch(props.customDictUrl, { method: 'PATCH', body, headers: csrfHeaders() });
          const data = await resp.json();
          if (data.status !== false) { addedToDict.value = true; emit('dict-added'); }
        } finally { addingToDict.value = false; }
      }

      function onGlossInput(e) { emit('update:modelValue', e.target.value); }

      const isDirty = computed(() => (props.modelValue ?? '') !== (props.savedValue ?? ''));

      const filteredSuggestions = computed(() => suggestions.value);

      const hasCustomEntry = computed(() =>
        query.value.trim() && !suggestions.value.some(item => item.value === query.value.trim())
      );

      watch(() => props.modelValue, () => { addedToDict.value = false; });

      return {
        open, query, loading, activeIndex,
        addingToDict, addedToDict,
        root, inputRef, glossRef, ddListRef,
        isDirty, filteredSuggestions, hasCustomEntry,
        close, onInputFocus, onQueryInput, onInputKeydown, onGlossKeydown,
        pick, pickCustom, addToDict, onGlossInput,
      };
    },
    template: `
      <div class="anno-field" :data-field="fieldKey" ref="root">

        <!-- Gloss: plain inline input (no autocomplete) -->
        <template v-if="!autocompleteUrls">
          <div :class="['anno-field-label', isDirty && 'anno-field-label--dirty']">{{ label }}</div>
          <input
            ref="glossRef"
            :class="['anno-input--inline', isDirty && 'anno-input--dirty']"
            :value="modelValue"
            @input="onGlossInput"
            @keydown="onGlossKeydown"
            autocomplete="off" spellcheck="false" placeholder="—"
          />
        </template>

        <!-- Autocomplete fields (lemma, POS, morph) -->
        <template v-else>
          <div :class="['anno-field-label',
            isDirty && !invalid && 'anno-field-label--dirty',
            invalid && !addedToDict && 'anno-field-label--invalid']">{{ label }}</div>
          <input
            ref="inputRef"
            :class="['anno-field-input',
              open && 'open',
              isDirty && !invalid && 'dirty',
              invalid && !addedToDict && 'invalid']"
            :value="open ? query : (modelValue || '')"
            :placeholder="open ? (modelValue || '—') : '—'"
            @focus="onInputFocus"
            @input="onQueryInput"
            @keydown="onInputKeydown"
            autocomplete="off" spellcheck="false"
          />

          <!-- Invalid popdown -->
          <div v-if="invalid && !addedToDict && !open" class="field-error-popdown">
            <div class="field-error-msg">
              <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
                <circle cx="6" cy="6" r="5.5" stroke="#c0392b"/>
                <path d="M6 3.5v3M6 8h.01" stroke="#c0392b" stroke-width="1.2" stroke-linecap="round"/>
              </svg>
              <span><code>{{ modelValue }}</code> not in {{ label }} list</span>
            </div>
            <button class="field-error-action" @mousedown.prevent="addToDict" :disabled="addingToDict">
              <span class="yellow-dot"></span>
              Add <strong style="font-family:'IBM Plex Mono',monospace;margin:0 3px">{{ modelValue }}</strong> to custom dictionary
            </button>
          </div>

          <!-- Suggestion dropdown -->
          <div v-if="open" class="anno-dropdown">
            <div class="dd-list" ref="ddListRef">
              <div v-if="loading" class="dd-item" style="color:var(--at-text-muted)">Loading…</div>
              <template v-else>
                <div
                  v-for="(item, idx) in filteredSuggestions"
                  :key="item.value"
                  :data-val="item.value"
                  :class="['dd-item', item.value === modelValue && 'selected', idx === activeIndex && 'active']"
                  @mousedown.prevent="pick(item)"
                >
                  <span>{{ item.value }}</span>
                  <span v-if="item.label !== item.value" class="dd-item-label">{{ item.label }}</span>
                </div>
                <div
                  v-if="hasCustomEntry"
                  :class="['dd-item', 'dd-item--custom', activeIndex === filteredSuggestions.length && 'active']"
                  @mousedown.prevent="pickCustom"
                >
                  <span>"{{ query }}"</span>
                  <span class="dd-item-label">Use custom value</span>
                </div>
                <div v-if="!filteredSuggestions.length && !hasCustomEntry" class="dd-item" style="color:var(--at-text-muted)">
                  No matches
                </div>
              </template>
            </div>
          </div>
        </template>

      </div>
    `,
  };

  // ── TokenRow ─────────────────────────────────────────────────────────────────

  const TokenRow = {
    name: 'TokenRow',
    components: { AnnotationField },
    props: {
      token: Object,
      visibleColumns: Array,
      urls: Object,
      page: Number,
    },
    emits: ['tab-row-next', 'tab-row-prev'],
    setup(props, { emit: rowEmit, expose }) {
      const state = reactive({
        lemma: props.token.lemma ?? '',
        POS:   props.token.POS   ?? '',
        morph: props.token.morph ?? '',
        gloss: props.token.gloss ?? '',
        similar: props.token.similar ?? 0,
        similarLink: props.token.similar_link ?? null,
        similarRecordLink: null,   // set only from save response → tokens_similar_to_record
        similarRecordCount: 0,
        changed: props.token.changed ?? false,
        saving: false,
        saveStatus: null,
        saveMessage: '',
        invalidFields: {},
        needs_review: props.token.needs_review ?? false,
        review_comment: props.token.review_comment ?? '',
        showReviewPanel: false,
        reviewSaving: false,
      });

      const saved = reactive({
        lemma: props.token.lemma ?? '',
        POS:   props.token.POS   ?? '',
        morph: props.token.morph ?? '',
        gloss: props.token.gloss ?? '',
      });

      const hasLemma   = computed(() => props.visibleColumns.includes('lemma'));
      const hasPOS     = computed(() => props.visibleColumns.includes('POS'));
      const hasMorph   = computed(() => props.visibleColumns.includes('morph'));
      const hasGloss   = computed(() => props.visibleColumns.includes('gloss'));
      const hasSimilar = computed(() => props.visibleColumns.includes('similar'));

      const rowClass = computed(() => ['at-row', state.changed && 'at-row--changed', state.needs_review && 'at-row--needs-review']);
      const simClass = computed(() => {
        if (state.similar > 100) return 'sim-badge sim-badge--many';
        if (state.similar > 0)   return 'sim-badge sim-badge--has';
        return 'sim-badge';
      });

      const acUrls = {
        lemma: props.urls.autocomplete?.lemma ?? null,
        POS:   props.urls.autocomplete?.POS   ?? null,
        morph: props.urls.autocomplete?.morph ?? null,
        gloss: props.urls.autocomplete?.gloss ?? null,
      };

      // Named refs for tab navigation
      const refLemma = ref(null);
      const refPOS   = ref(null);
      const refMorph = ref(null);
      const refGloss = ref(null);

      const orderedFieldRefs = computed(() => {
        const pairs = [
          [hasLemma,  refLemma],
          [hasPOS,    refPOS],
          [hasMorph,  refMorph],
          [hasGloss,  refGloss],
        ];
        return pairs.filter(([vis]) => vis.value).map(([, r]) => r);
      });

      function focusByKey(key) {
        const map = { lemma: refLemma, POS: refPOS, morph: refMorph, gloss: refGloss };
        map[key]?.value?.focus();
      }

      function onTabNext(fromKey) {
        const refs = orderedFieldRefs.value;
        const keys = ['lemma', 'POS', 'morph', 'gloss'].filter(k => props.visibleColumns.includes(k === 'POS' ? 'POS' : k));
        const idx = keys.indexOf(fromKey);
        if (idx >= 0 && idx < refs.length - 1) refs[idx + 1].value?.focus();
        else rowEmit('tab-row-next');
      }

      function onTabPrev(fromKey) {
        const refs = orderedFieldRefs.value;
        const keys = ['lemma', 'POS', 'morph', 'gloss'].filter(k => props.visibleColumns.includes(k === 'POS' ? 'POS' : k));
        const idx = keys.indexOf(fromKey);
        if (idx > 0) refs[idx - 1].value?.focus();
        else rowEmit('tab-row-prev');
      }

      function focusFirst() { orderedFieldRefs.value[0]?.value?.focus(); }
      function focusLast()  { const r = orderedFieldRefs.value; r[r.length - 1]?.value?.focus(); }

      async function save() {
        // Commit any value the user has typed but not yet confirmed via pick/Enter
        [refLemma, refPOS, refMorph, refGloss].forEach(r => r.value?.flush?.());
        await nextTick();
        const unchanged =
          state.lemma === saved.lemma &&
          state.POS   === saved.POS   &&
          state.morph === saved.morph &&
          state.gloss === saved.gloss;
        if (unchanged) {
          state.saveStatus = 'unchanged';
          return;
        }
        state.saving = true;
        state.saveStatus = null;
        state.invalidFields = {};
        state.similarRecordLink = null;
        state.similarRecordCount = 0;
        const body = new FormData();
        if (hasLemma.value)  body.append('lemma', state.lemma);
        if (hasPOS.value)    body.append('POS',   state.POS);
        if (hasMorph.value)  body.append('morph', state.morph);
        if (hasGloss.value)  body.append('gloss', state.gloss);
        try {
          const resp = await fetch(`${props.urls.save}${props.token.id}`, { method: 'POST', body, headers: csrfHeaders() });
          const data = await resp.json();
          if (resp.ok) {
            state.changed = true;
            state.saveStatus = 'ok';
            state.similarRecordLink = null;
            state.similarRecordCount = 0;
            if (data.similar) {
              state.similar = data.similar.count;
              state.similarLink = data.similar.link;
              if (data.similar.count > 0) {
                state.similarRecordLink = data.similar.link;
                state.similarRecordCount = data.similar.count;
              }
            }
            if (data.token) {
              state.lemma = data.token.lemma ?? '';
              state.POS   = data.token.POS   ?? '';
              state.morph = data.token.morph ?? '';
              state.gloss = data.token.gloss ?? '';
            }
            saved.lemma = state.lemma; saved.POS = state.POS;
            saved.morph = state.morph; saved.gloss = state.gloss;
          } else if (resp.status === 403 && data.details) {
            state.saveStatus = 'error';
            state.saveMessage = data.message || 'Invalid value';
            const inv = {};
            for (const [field, valid] of Object.entries(data.details)) {
              if (valid === false) inv[field.toLowerCase()] = true;
            }
            state.invalidFields = inv;
          } else if (resp.status === 400) {
            state.saveStatus = 'info';
            state.saveMessage = data.message || 'No value was changed';
          } else {
            state.saveStatus = 'error';
            state.saveMessage = data.message || 'Error';
          }
        } catch (e) {
          state.saveStatus = 'error'; state.saveMessage = 'Network error';
        } finally {
          state.saving = false;
        }
      }

      function onDictAdded(field) {
        const inv = { ...state.invalidFields };
        delete inv[field.toLowerCase()];
        state.invalidFields = inv;
        if (Object.keys(state.invalidFields).length === 0) save();
      }

      async function saveReview(markForReview) {
        state.reviewSaving = true;
        try {
          const body = new FormData();
          body.append('needs_review', markForReview ? 'true' : 'false');
          if (markForReview && state.review_comment) {
            body.append('review_comment', state.review_comment);
          }
          const resp = await fetch(`${props.urls.review}${props.token.id}`, { method: 'POST', body, headers: csrfHeaders() });
          if (resp.ok) {
            const data = await resp.json();
            state.needs_review = data.token.needs_review;
            state.review_comment = data.token.review_comment ?? '';
            state.showReviewPanel = false;
          }
        } finally {
          state.reviewSaving = false;
        }
      }

      expose({ focusFirst, focusLast });

      return {
        state, saved, rowClass, simClass,
        hasLemma, hasPOS, hasMorph, hasGloss, hasSimilar,
        acUrls, refLemma, refPOS, refMorph, refGloss,
        save, onDictAdded, onTabNext, onTabPrev, saveReview,
      };
    },
    template: `
      <div :class="rowClass" :id="'token_' + token.id + '_row'" :data-token-order="token.order_id">

        <!-- Col 1: ID spans 2 rows -->
        <div class="at-cell at-cell--id">
          <a :href="'#tok' + token.order_id" :id="'tok' + token.order_id" class="at-order-id" tabindex="-1">{{ token.token_reference ?? token.order_id }}</a>
          <button :class="['at-review-toggle', state.needs_review && 'at-review-toggle--active']"
                  :title="state.needs_review ? (state.review_comment || 'Flagged for review') : 'Mark for review'"
                  @click="state.showReviewPanel = !state.showReviewPanel" tabindex="-1">⚑</button>
        </div>

        <!-- Col 2: Form spans 2 rows -->
        <div class="at-cell at-cell--form">{{ token.form }}</div>

        <!-- Col 3 row 1: Context -->
        <div class="at-cell at-cell--ctx">
          <span v-if="token.left_context" class="ctx-side">{{ token.left_context }}&nbsp;</span>
          <span class="ctx-hi">{{ token.form }}</span>
          <span v-if="token.right_context" class="ctx-side">&nbsp;{{ token.right_context }}</span>
        </div>

        <!-- Col 4 row 1: Similar -->
        <div class="at-cell at-cell--sim">
          <a v-if="hasSimilar && state.similar > 0 && state.similarLink"
             :href="state.similarLink" :class="simClass" tabindex="-1">{{ state.similar }}</a>
          <span v-else-if="hasSimilar" :class="simClass">{{ state.similar }}</span>
        </div>

        <!-- Col 3 row 2: Annotation fields -->
        <div class="at-cell at-cell--anno">
          <AnnotationField v-if="hasLemma"
            ref="refLemma" label="Lemma" field-key="lemma"
            v-model="state.lemma" :saved-value="saved.lemma"
            :autocomplete-urls="acUrls.lemma" field-type="text"
            :invalid="!!state.invalidFields['lemma']"
            :custom-dict-url="urls.custom_dict"
            @dict-added="onDictAdded('lemma')"
            @tab-next="onTabNext" @tab-prev="onTabPrev" @save="save"
          />
          <AnnotationField v-if="hasPOS"
            ref="refPOS" label="POS" field-key="POS"
            v-model="state.POS" :saved-value="saved.POS"
            :autocomplete-urls="acUrls.POS" field-type="text"
            :invalid="!!state.invalidFields['pos']"
            :custom-dict-url="urls.custom_dict"
            @dict-added="onDictAdded('POS')"
            @tab-next="onTabNext" @tab-prev="onTabPrev" @save="save"
          />
          <AnnotationField v-if="hasMorph"
            ref="refMorph" label="Morph" field-key="morph"
            v-model="state.morph" :saved-value="saved.morph"
            :autocomplete-urls="acUrls.morph" field-type="morph"
            :invalid="!!state.invalidFields['morph']"
            :custom-dict-url="urls.custom_dict"
            @dict-added="onDictAdded('morph')"
            @tab-next="onTabNext" @tab-prev="onTabPrev" @save="save"
          />
          <AnnotationField v-if="hasGloss"
            ref="refGloss" label="Gloss" field-key="gloss"
            v-model="state.gloss" :saved-value="saved.gloss"
            :autocomplete-urls="acUrls.gloss" field-type="text"
            @tab-next="onTabNext" @tab-prev="onTabPrev" @save="save"
          />
        </div>

        <!-- Col 4 row 2: Save -->
        <div class="at-cell at-cell--act">
          <button class="save-btn" @click="save" :disabled="state.saving" tabindex="-1">
            {{ state.saving ? '…' : 'Save' }}
          </button>
          <span v-if="state.saveStatus === 'ok'" class="save-status save-ok" title="Saved">✓</span>
          <span v-if="state.saveStatus === 'unchanged'" class="save-status save-unchanged" title="Nothing changed">=</span>
          <span v-if="state.saveStatus === 'info'" class="save-status save-info">{{ state.saveMessage }}</span>
          <span v-if="state.saveStatus === 'error'"
                class="save-status save-err" :title="state.saveMessage">✗</span>
        </div>

        <!-- Row 3: Similar hint — only shown after a save when the backend reports remaining similar tokens -->
        <a v-if="state.similarRecordLink"
           :id="'token_' + token.id + '_similar_hint'"
           :href="state.similarRecordLink" class="at-cell at-sim-hint" tabindex="-1">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="flex-shrink:0">
            <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
            <path d="M8 7v5M8 5h.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span>{{ state.similarRecordCount }} similar token{{ state.similarRecordCount > 1 ? 's' : '' }} share this form — click to apply the same correction</span>
        </a>

        <!-- Review panel — full-width row, shown when user opens the review flag form -->
        <div v-if="state.showReviewPanel" class="at-cell at-review-panel">
          <textarea v-model="state.review_comment" placeholder="Optional comment…" rows="2"></textarea>
          <div class="at-review-actions">
            <button class="at-review-flag-btn" @click="saveReview(true)" :disabled="state.reviewSaving">{{ state.reviewSaving ? '…' : 'Flag for review' }}</button>
            <button v-if="state.needs_review" class="at-review-remove-btn" @click="saveReview(false)" :disabled="state.reviewSaving">Remove flag</button>
            <button class="at-review-cancel-btn" @click="state.showReviewPanel = false">Cancel</button>
          </div>
        </div>

        <!-- Col 5: ⋯ menu spans 2 rows -->
        <div class="at-cell at-cell--dd">
          <div class="at-dropdown">
            <button class="at-dd-toggle" type="button" title="More options" tabindex="-1">⋯</button>
            <ul class="at-dd-menu">
              <li><a :href="urls.edit   + token.id" tabindex="-1">Edit form</a></li>
              <li><a :href="urls.remove + token.id" tabindex="-1">Delete row</a></li>
              <li><a :href="urls.insert + token.id" tabindex="-1">Add token after</a></li>
              <li><a :href="urls.bookmark + '?token_id=' + token.id + '&page=' + page" tabindex="-1">Bookmark</a></li>
              <li><a href="#" tabindex="-1" @click.prevent="state.showReviewPanel = !state.showReviewPanel">{{ state.needs_review ? 'Edit review flag' : 'Mark for review' }}</a></li>
              <li v-if="state.needs_review"><a href="#" tabindex="-1" @click.prevent="saveReview(false)">Remove review flag</a></li>
            </ul>
          </div>
        </div>

      </div>
    `,
  };

  // ── Pagination component ─────────────────────────────────────────────────────

  function iterPages(page, pages) {
    const result = [];
    let last = 0;
    for (let p = 1; p <= pages; p++) {
      if (p <= 2 || p > pages - 2 || Math.abs(p - page) <= 2) {
        if (last && last + 1 !== p) result.push(null);
        result.push(p);
        last = p;
      }
    }
    return result;
  }

  const Pagination = {
    props: { page: Number, pages: Number, total: Number, loading: Boolean },
    emits: ['goto'],
    setup(props, { emit }) {
      const goInput = ref('');
      const pageList = computed(() => iterPages(props.page, props.pages));
      function go(n) {
        const p = parseInt(n);
        if (p >= 1 && p <= props.pages) emit('goto', p);
      }
      function submitGo() { go(goInput.value); goInput.value = ''; }
      return { pageList, goInput, go, submitGo };
    },
    template: `
      <div class="at-pagination">
        <nav aria-label="Page navigation">
          <ul class="pagination pagination-sm mb-0">
            <li class="page-item" :class="{ disabled: page <= 1 || loading }">
              <a class="page-link" href="#" @click.prevent="go(page - 1)">‹</a>
            </li>
            <template v-for="p in pageList" :key="p ?? 'ellipsis-' + Math.random()">
              <li v-if="p === null" class="page-item disabled"><span class="page-link">…</span></li>
              <li v-else class="page-item page-nb" :class="{ active: p === page }">
                <a class="page-link" href="#" @click.prevent="go(p)">{{ p }}</a>
              </li>
            </template>
            <li class="page-item page-next" :class="{ disabled: page >= pages || loading }">
              <a class="page-link" href="#" @click.prevent="go(page + 1)">›</a>
            </li>
          </ul>
        </nav>
        <form class="at-pagination-goto" @submit.prevent="submitGo">
          <button class="btn btn-primary btn-sm" type="submit" :disabled="loading">Go to</button>
          <input type="number" v-model="goInput" min="1" :max="pages" placeholder="Page" class="form-control form-control-sm" style="width:70px" />
        </form>
        <span class="at-pagination-total">{{ total }} token{{ total !== 1 ? 's' : '' }}</span>
      </div>
    `,
  };

  // ── Root app ─────────────────────────────────────────────────────────────────

  const config = JSON.parse(document.getElementById('pyrrha-config').textContent);

  createApp({
    components: { TokenRow, Pagination },
    setup() {
      const visibleColumns = config.visible_columns;
      const colLabels = { lemma: 'Lemma', POS: 'POS', morph: 'Morph', gloss: 'Gloss' };
      const annoHeader = ['lemma', 'POS', 'morph', 'gloss']
        .filter(k => visibleColumns.includes(k))
        .map(k => colLabels[k])
        .join(' · ');

      const tokens    = ref([]);
      const page      = ref(1);
      const pages     = ref(1);
      const total     = ref(0);
      const loading   = ref(true);
      const loadError = ref(null);

      async function fetchPage(num) {
        loading.value = true;
        loadError.value = null;
        const url = new URL(config.urls.data, window.location.href);
        for (const [k, v] of new URLSearchParams(window.location.search)) {
          if (k !== 'page') url.searchParams.set(k, v);
        }
        url.searchParams.set('page', String(num));
        try {
          const resp = await fetch(url.toString());
          if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
          const data = await resp.json();
          tokens.value = data.tokens;
          page.value   = data.page;
          pages.value  = data.pages;
          total.value  = data.total;
          const newUrl = new URL(window.location.href);
          newUrl.searchParams.set('page', String(data.page));
          history.pushState({ page: data.page }, '', newUrl.toString());
        } catch (e) {
          loadError.value = e.message || 'Failed to load tokens';
        } finally {
          loading.value = false;
        }
      }

      onMounted(() => {
        const p = parseInt(new URLSearchParams(window.location.search).get('page') || '1');
        fetchPage(p);
        window.addEventListener('popstate', e => fetchPage(e.state?.page || 1));
      });

      const rowRefs = ref([]);

      function onTabRowNext(idx) {
        const next = rowRefs.value[idx + 1];
        if (next) next.focusFirst();
      }
      function onTabRowPrev(idx) {
        const prev = rowRefs.value[idx - 1];
        if (prev) prev.focusLast();
      }

      return {
        tokens, page, pages, total, loading, loadError,
        visibleColumns, urls: config.urls, annoHeader,
        fetchPage, rowRefs, onTabRowNext, onTabRowPrev,
      };
    },
    template: `
      <div>
        <Pagination v-if="pages > 1 || total > 0" :page="page" :pages="pages" :total="total" :loading="loading" @goto="fetchPage" />
        <div class="at-table-wrap mt-2">
          <div v-if="loading" class="at-loading">Loading…</div>
          <div v-else-if="loadError" class="at-load-error">{{ loadError }}</div>
          <template v-else>
            <div class="at-head">
              <div class="at-th at-th--id">#</div>
              <div class="at-th at-th--form">Form</div>
              <div class="at-th at-th--ctx">Context</div>
              <div class="at-th at-th--sim">Similar <br/>tokens</div>
              <div class="at-th at-th--anno">{{ annoHeader }}</div>
              <div class="at-th at-th--act">Save</div>
              <div class="at-th at-th--dd"></div>
            </div>
            <TokenRow
              v-for="(token, idx) in tokens"
              :key="token.id"
              :ref="el => rowRefs[idx] = el"
              :token="token"
              :visible-columns="visibleColumns"
              :urls="urls"
              :page="page"
              @tab-row-next="onTabRowNext(idx)"
              @tab-row-prev="onTabRowPrev(idx)"
            />
          </template>
        </div>
        <Pagination v-if="pages > 1 || total > 0" :page="page" :pages="pages" :total="total" :loading="loading" @goto="fetchPage" class="mt-2" />
      </div>
    `,
  }).mount('#annotation-table');

}());
