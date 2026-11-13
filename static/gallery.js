'use strict';
(() => {
  const gallery = document.getElementById('galeria');
  if (!gallery) return;
  const photos = [...gallery.querySelectorAll('.gallery-photo')];
  const filters = gallery.querySelector('.gallery-filters');
  const count = gallery.querySelector('.gallery-count');
  const dialog = document.getElementById('photo-viewer');
  const image = document.getElementById('viewer-image');
  const counter = document.getElementById('viewer-counter');
  const source = document.getElementById('viewer-source');
  let selected = [];
  let current = 0;
  let origin;
  function chooseEdition(edition) {
    selected = photos.filter(photo => photo.dataset.galleryEdition === edition);
    photos.forEach(photo => { photo.hidden = photo.dataset.galleryEdition !== edition; });
    filters.querySelectorAll('button').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.edition === edition)));
    count.textContent = `${selected.length} fotos selecionadas da ${edition}ª edição`;
  }
  filters.hidden = false;
  count.hidden = false;
  filters.querySelectorAll('button').forEach(button => button.addEventListener('click', () => chooseEdition(button.dataset.edition)));
  chooseEdition('2');
  if (typeof dialog.showModal !== 'function') return; // Regular image links remain usable.
  function display(index) {
    current = (index + selected.length) % selected.length;
    const photo = selected[current];
    image.src = photo.getAttribute('href');
    image.alt = photo.dataset.caption;
    source.href = photo.dataset.source;
    counter.textContent = `${current + 1} de ${selected.length} · ${photo.dataset.galleryEdition}ª edição`;
  }
  photos.forEach(photo => photo.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    origin = photo;
    display(selected.indexOf(photo));
    dialog.showModal();
    document.body.classList.add('photo-viewer-open');
    dialog.querySelector('.viewer-close').focus();
  }));
  dialog.querySelector('.viewer-close').addEventListener('click', () => dialog.close());
  dialog.querySelector('.viewer-prev').addEventListener('click', () => display(current - 1));
  dialog.querySelector('.viewer-next').addEventListener('click', () => display(current + 1));
  dialog.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft') { event.preventDefault(); display(current - 1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); display(current + 1); }
  });
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => {
    document.body.classList.remove('photo-viewer-open');
    image.removeAttribute('src');
    if (origin) origin.focus({preventScroll: true});
  });
  let touchStart = null;
  image.addEventListener('touchstart', event => {
    if (event.touches.length === 1) touchStart = {x:event.touches[0].clientX,y:event.touches[0].clientY};
  }, {passive:true});
  image.addEventListener('touchend', event => {
    if (!touchStart || !event.changedTouches.length) return;
    const dx = event.changedTouches[0].clientX - touchStart.x;
    const dy = event.changedTouches[0].clientY - touchStart.y;
    if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy)) display(current + (dx < 0 ? 1 : -1));
    touchStart = null;
  }, {passive:true});
})();
