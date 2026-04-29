/* Pyrrha similar-to-record bulk selection table — Vue 3 CDN, no build step */
(function () {
  'use strict';

  const { createApp, ref, computed, onMounted } = Vue;

  const cfg = JSON.parse(document.getElementById('pyrrha-config').textContent);
  const rec = cfg.record || {};

  const app = createApp({
    setup() {
      const tokens      = ref([]);
      const page        = ref(1);
      const pages       = ref(1);
      const total       = ref(0);
      const loading     = ref(true);
      const loadError   = ref(null);
      const selected    = ref(new Set());
      const applying    = ref(false);
      const applyStatus  = ref(null);
      const applyMessage = ref('');

      const visible  = cfg.visible_columns || [];
      const hasLemma = visible.includes('lemma');
      const hasPOS   = visible.includes('POS');
      const hasMorph = visible.includes('morph');
      const hasGloss = visible.includes('gloss');

      const changesLemma = rec.lemma !== rec.lemma_new;
      const changesPOS   = rec.POS   !== rec.POS_new;
      const changesMorph = rec.morph !== rec.morph_new;

      async function fetchPage(p) {
        loading.value   = true;
        loadError.value = null;
        try {
          const data = await fetch(`${cfg.data_url}?page=${p}&limit=100`).then(r => r.json());
          tokens.value   = data.tokens;
          page.value     = data.page;
          pages.value    = data.pages;
          total.value    = data.total;
          selected.value = new Set(data.tokens.map(t => t.id));
        } catch (_) {
          loadError.value = 'Failed to load tokens.';
        } finally {
          loading.value = false;
        }
      }

      onMounted(() => fetchPage(1));

      const allSelected = computed(() =>
        tokens.value.length > 0 && tokens.value.every(t => selected.value.has(t.id))
      );

      function toggleAll() {
        selected.value = allSelected.value
          ? new Set()
          : new Set(tokens.value.map(t => t.id));
      }

      function toggleToken(id) {
        const s = new Set(selected.value);
        if (s.has(id)) s.delete(id); else s.add(id);
        selected.value = s;
      }

      async function applySelected() {
        if (!selected.value.size) return;
        applying.value    = true;
        applyStatus.value = null;
        try {
          const resp = await fetch(cfg.apply_url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word_tokens: [...selected.value] }),
          });
          if (resp.ok) {
            const updated = await resp.json();
            applyStatus.value  = 'ok';
            applyMessage.value = `${updated.length} token${updated.length > 1 ? 's' : ''} updated.`;
            await fetchPage(page.value);
          } else {
            applyStatus.value  = 'error';
            applyMessage.value = 'Update failed.';
          }
        } catch (_) {
          applyStatus.value  = 'error';
          applyMessage.value = 'Network error.';
        } finally {
          applying.value = false;
        }
      }

      return {
        tokens, page, pages, total, loading, loadError,
        selected, applying, applyStatus, applyMessage,
        allSelected, hasLemma, hasPOS, hasMorph, hasGloss,
        changesLemma, changesPOS, changesMorph, rec,
        fetchPage, toggleAll, toggleToken, applySelected,
      };
    },

    template: `
      <div class="srt-wrap">

        <!-- Toolbar -->
        <div class="srt-toolbar">
          <label class="srt-check-label">
            <input type="checkbox" :checked="allSelected" @change="toggleAll" />
            {{ allSelected ? 'Deselect all' : 'Select all' }}
          </label>
          <span class="srt-count">{{ selected.size }} / {{ total }} selected</span>
          <button class="srt-apply-btn" @click="applySelected"
                  :disabled="applying || !selected.size">
            {{ applying ? 'Applying…' : 'Apply to selected' }}
          </button>
          <span v-if="applyStatus === 'ok'"    class="srt-status srt-status--ok">✓ {{ applyMessage }}</span>
          <span v-if="applyStatus === 'error'" class="srt-status srt-status--err">✗ {{ applyMessage }}</span>
        </div>

        <div v-if="loading"             class="srt-loading">Loading…</div>
        <div v-else-if="loadError"      class="srt-loading">{{ loadError }}</div>
        <div v-else-if="!tokens.length" class="srt-loading">No similar tokens remaining.</div>

        <div v-else class="at-table" id="annotation-table">

          <!-- Header -->
          <div class="at-head at-head--bulk">
            <div class="at-th at-th--id">#</div>
            <div class="at-th at-th--form">Form</div>
            <div class="at-th at-th--ctx">Context</div>
            <div class="at-th at-th--anno" style="display:flex;align-items:center;padding:0">
              <div v-if="hasLemma" class="anno-field at-th-field" data-field="lemma">Lemma</div>
              <div v-if="hasPOS"   class="anno-field at-th-field" data-field="POS">POS</div>
              <div v-if="hasMorph" class="anno-field at-th-field" data-field="morph">Morph</div>
              <div v-if="hasGloss" class="anno-field at-th-field" data-field="gloss">Gloss</div>
            </div>
          </div>

          <div v-for="tok in tokens" :key="tok.id"
               :class="['at-row at-row--bulk', selected.has(tok.id) && 'at-row--selected', tok.changed && 'at-row--changed']"
               @click="toggleToken(tok.id)">

            <!-- Col 1: checkbox + order_id, spans all 3 rows -->
            <div class="at-cell at-cell--id" style="cursor:pointer;flex-direction:column;gap:4px">
              <input type="checkbox" :checked="selected.has(tok.id)"
                     @click.stop @change="toggleToken(tok.id)" />
              <span class="at-order-id">{{ tok.order_id }}</span>
            </div>

            <!-- Col 2: form spans all 3 rows -->
            <div class="at-cell at-cell--form">{{ tok.form }}</div>

            <!-- Col 3 row 1: context -->
            <div class="at-cell at-cell--ctx">
              <span v-if="tok.left_context" class="ctx-side">{{ tok.left_context }}&nbsp;</span>
              <span class="ctx-hi">{{ tok.form }}</span>
              <span v-if="tok.right_context" class="ctx-side">&nbsp;{{ tok.right_context }}</span>
            </div>

            <!-- Col 3 row 2: current annotation values (read-only) -->
            <div class="at-cell at-cell--anno">
              <div v-if="hasLemma" class="anno-field" data-field="lemma">
                <span :class="['anno-field-input', changesLemma && 'anno-val--changing']">{{ tok.lemma || '—' }}</span>
              </div>
              <div v-if="hasPOS" class="anno-field" data-field="POS">
                <span :class="['anno-field-input', changesPOS && 'anno-val--changing']">{{ tok.POS || '—' }}</span>
              </div>
              <div v-if="hasMorph" class="anno-field" data-field="morph">
                <span :class="['anno-field-input', changesMorph && 'anno-val--changing']">{{ tok.morph || '—' }}</span>
              </div>
              <div v-if="hasGloss" class="anno-field" data-field="gloss">
                <span class="anno-field-input">{{ tok.gloss || '—' }}</span>
              </div>
            </div>

            <!-- Col 3 row 3: new values to apply -->
            <div class="at-cell at-cell--anno at-cell--anno-new">
              <div v-if="hasLemma && changesLemma" class="anno-field anno-field--new" data-field="lemma">
                <span class="anno-field-input anno-val--new">{{ rec.lemma_new || '—' }}</span>
              </div>
              <div v-if="hasPOS && changesPOS" class="anno-field anno-field--new" data-field="POS">
                <span class="anno-field-input anno-val--new">{{ rec.POS_new || '—' }}</span>
              </div>
              <div v-if="hasMorph && changesMorph" class="anno-field anno-field--new" data-field="morph">
                <span class="anno-field-input anno-val--new">{{ rec.morph_new || '—' }}</span>
              </div>
            </div>

          </div>
        </div>

        <!-- Pagination -->
        <div v-if="pages > 1" class="at-pagination mt-2">
          <button class="page-link" :disabled="page <= 1" @click="fetchPage(page - 1)">‹</button>
          <span class="at-pagination-total">Page {{ page }} / {{ pages }}</span>
          <button class="page-link" :disabled="page >= pages" @click="fetchPage(page + 1)">›</button>
        </div>

      </div>
    `,
  });

  app.mount('#similar-record-table');
})();
