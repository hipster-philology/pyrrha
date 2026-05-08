/* Pyrrha list browser — Vue 3 CDN, no build step */
(function () {
  'use strict';

  const { createApp, ref, computed, onMounted } = Vue;

  function createListBrowser(mountId, configScriptId) {
    const configEl = document.getElementById(configScriptId);
    if (!configEl || !document.getElementById(mountId)) return;
    const config = JSON.parse(configEl.textContent);

    createApp({
      setup() {
        const items   = ref([]);
        const page    = ref(1);
        const pages   = ref(1);
        const total   = ref(0);
        const perPage = ref(config.per_page || 20);
        const search  = ref('');
        const sortKey = ref(config.default_sort || '');
        const sortDir = ref(config.default_sort_dir || 'asc');
        const loading = ref(false);
        const error   = ref(null);

        let debounceTimer = null;

        function sortBy(col) {
          if (!col.sortable) return;
          if (sortKey.value === col.key) {
            sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc';
          } else {
            sortKey.value = col.key;
            sortDir.value = 'asc';
          }
          page.value = 1;
          fetchItems();
        }

        async function fetchItems() {
          loading.value = true;
          error.value   = null;
          try {
            const url = new URL(config.api_url, window.location.origin);
            url.searchParams.set('page', page.value);
            url.searchParams.set('per_page', perPage.value);
            url.searchParams.set('search', search.value);
            if (sortKey.value) {
              url.searchParams.set('sort', sortKey.value);
              url.searchParams.set('order', sortDir.value);
            }
            const resp = await fetch(url.toString());
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            items.value = data.items;
            pages.value = data.pages;
            total.value = data.total;
          } catch (e) {
            error.value = e.message;
          } finally {
            loading.value = false;
          }
        }

        function onSearch() {
          clearTimeout(debounceTimer);
          debounceTimer = setTimeout(() => { page.value = 1; fetchItems(); }, 300);
        }

        function goTo(p) {
          if (p < 1 || p > pages.value) return;
          page.value = p;
          fetchItems();
        }

        const pageNumbers = computed(() => {
          const n = pages.value, p = page.value;
          if (n <= 7) return Array.from({ length: n }, (_, i) => i + 1);
          const s = new Set([1, n, p, p - 1, p + 1, p - 2, p + 2]);
          return [...s].filter(x => x >= 1 && x <= n).sort((a, b) => a - b);
        });

        onMounted(fetchItems);

        return { items, page, pages, total, perPage, search, sortKey, sortDir, loading, error, config, pageNumbers, onSearch, goTo, sortBy };
      },

      template: `
<div>
  <div class="d-flex align-items-center mb-3 flex-wrap" style="gap:.5rem">
    <input
      type="search"
      class="form-control form-control-sm"
      style="max-width:280px"
      :placeholder="config.search_placeholder || 'Search…'"
      v-model="search"
      @input="onSearch"
    />
    <span class="text-muted small">
      <span v-if="loading"><i class="fa fa-spinner fa-spin"></i></span>
      <span v-else>{{ total }} result<span v-if="total !== 1">s</span></span>
    </span>
  </div>

  <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
  <div v-else-if="!loading && items.length === 0" class="text-muted small">No results.</div>
  <div v-else>
    <table class="table table-hover table-sm">
      <thead class="thead-light">
        <tr>
          <th v-for="col in config.columns" :key="col.key"
              :style="col.sortable ? 'cursor:pointer;user-select:none' : ''"
              @click="sortBy(col)">
            {{ col.label }}
            <span v-if="col.sortable">
              <i v-if="sortKey === col.key && sortDir === 'asc'"  class="fa fa-sort-asc ml-1"></i>
              <i v-else-if="sortKey === col.key && sortDir === 'desc'" class="fa fa-sort-desc ml-1"></i>
              <i v-else class="fa fa-sort ml-1 text-muted"></i>
            </span>
          </th>
          <th v-if="config.actions && config.actions.length" class="text-right"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" :title="config.title_key ? item[config.title_key] : undefined">
          <td v-for="col in config.columns" :key="col.key" :class="col.class || ''">
            <template v-if="col.icon_key">
              <a :href="item[col.link_key]" :title="col.label || ''">
                <i :class="'fa ' + item[col.icon_key]"></i>
              </a>
            </template>
            <template v-else-if="col.link_key && item[col.link_key]">
              <a :href="item[col.link_key]">{{ item[col.key] ?? '—' }}</a>
            </template>
            <template v-else>{{ item[col.key] ?? '—' }}</template>
          </td>
          <td v-if="config.actions && config.actions.length" class="text-right text-nowrap">
            <template v-for="action in config.actions" :key="action.label">
              <a
                v-if="item[action.link_key]"
                :href="item[action.link_key]"
                :title="action.label"
                class="btn btn-sm btn-outline-secondary mr-1"
                style="padding:1px 6px"
              ><i :class="'fa ' + action.icon"></i></a>
            </template>
          </td>
        </tr>
      </tbody>
    </table>

    <nav v-if="pages > 1" aria-label="Pagination">
      <ul class="pagination pagination-sm">
        <li class="page-item" :class="{disabled: page === 1}">
          <a class="page-link" href="#" @click.prevent="goTo(page - 1)">&laquo;</a>
        </li>
        <template v-for="(p, idx) in pageNumbers" :key="p">
          <li v-if="idx > 0 && p - pageNumbers[idx-1] > 1" class="page-item disabled">
            <span class="page-link">…</span>
          </li>
          <li class="page-item" :class="{active: p === page}">
            <a class="page-link" href="#" @click.prevent="goTo(p)">{{ p }}</a>
          </li>
        </template>
        <li class="page-item" :class="{disabled: page === pages}">
          <a class="page-link next-link" href="#" @click.prevent="goTo(page + 1)">&raquo;</a>
        </li>
      </ul>
    </nav>
  </div>
</div>
      `
    }).mount('#' + mountId);
  }

  window.createListBrowser = createListBrowser;
})();
