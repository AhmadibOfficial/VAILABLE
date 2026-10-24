'use strict';
const search = document.querySelector('#search');
if (search) {
  const category = document.querySelector('#category');
  const filter = () => {
    let count = 0;
    for (const card of document.querySelectorAll('.card')) {
      card.hidden = !card.dataset.search.includes(search.value.trim().toLowerCase()) ||
        Boolean(category.value && card.dataset.category !== category.value);
      if (!card.hidden) count++;
    }
    document.querySelector('#results').textContent = `${count} capabilities`;
    document.querySelector('#empty').hidden = count !== 0;
  };
  search.addEventListener('input', filter);
  category.addEventListener('change', filter);
  document.querySelector('#search-form').addEventListener('submit', e => e.preventDefault());
}
const form = document.querySelector('#merge-form');
if (form) {
  let files = [];
  let busy = false;
  let downloadUrl;
  const picker = document.querySelector('#files');
  const list = document.querySelector('#file-list');
  const submit = document.querySelector('#merge-button');
  const status = document.querySelector('#merge-status');
  const download = document.querySelector('#download');
  const resetDownload = () => {
    download.hidden = true;
    download.removeAttribute('href');
    if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    downloadUrl = undefined;
  };
  const render = () => {
    list.replaceChildren();
    files.forEach((file, index) => {
      const row = document.createElement('li');
      const name = document.createElement('span');
      name.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KiB) `;
      row.append(name);
      for (const [label, offset] of [['Move up', -1], ['Move down', 1]]) {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = label;
        button.setAttribute('aria-label', `${label}: ${file.name}`);
        button.disabled = busy || index + offset < 0 || index + offset >= files.length;
        button.addEventListener('click', () => {
          [files[index], files[index + offset]] = [files[index + offset], files[index]];
          resetDownload();
          status.textContent = 'File order updated.';
          render();
          list.children[index + offset].querySelector('button:not(:disabled)').focus();
        });
        row.append(button);
      }
      list.append(row);
    });
    submit.disabled = busy || files.length < 2 || files.length > 10;
    picker.disabled = busy;
  };
  picker.addEventListener('change', () => {
    files = Array.from(picker.files);
    resetDownload();
    status.textContent = files.length > 10 ? 'Choose at most 10 PDFs.' : '';
    render();
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (busy || submit.disabled) return;
    resetDownload();
    if (files.some(file => !file.name.toLowerCase().endsWith('.pdf') || file.size === 0 || file.size > 5 * 1024 ** 2) || files.reduce((n, file) => n + file.size, 0) > 19.9 * 1024 ** 2) {
      status.textContent = 'Choose nonempty PDFs within the displayed limits.';
      return;
    }
    busy = true;
    render();
    status.textContent = 'Uploading and merging PDFs…';
    const body = new FormData();
    files.forEach(file => body.append('files', file, file.name));
    try {
      const response = await fetch('/api/merge', {method: 'POST', body});
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(typeof error.detail === 'string' ? error.detail : 'Merge failed. Please try again.');
      }
      if (!response.headers.get('content-type')?.startsWith('application/pdf')) throw new Error('Server returned an unexpected response.');
      const blob = await response.blob();
      if (!(await blob.slice(0, 5).text()).startsWith('%PDF-')) throw new Error('Server returned an invalid PDF.');
      downloadUrl = URL.createObjectURL(blob);
      download.href = downloadUrl;
      download.hidden = false;
      status.textContent = 'Merge complete. Download and review your PDF.';
    } catch (error) {
      status.textContent = error instanceof TypeError ? 'Could not reach the server. Please try again.' : error.message;
    } finally {
      busy = false;
      render();
    }
  });
  window.addEventListener('pagehide', resetDownload);
}
