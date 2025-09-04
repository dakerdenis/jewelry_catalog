(function () {
  const btn   = document.getElementById('openVideo');
  const modal = document.getElementById('videoModal');
  const slot  = document.getElementById('videoPlayer');

  if (!btn || !modal || !slot) return;

  // Универсально выдергиваем ID из watch/shorts/youtu.be
  function getYouTubeId(url) {
    try {
      const u = new URL(url);
      if (u.hostname.includes('youtu.be')) return u.pathname.slice(1);
      if (u.pathname.startsWith('/shorts/')) return u.pathname.split('/shorts/')[1].split('/')[0];
      if (u.searchParams.get('v')) return u.searchParams.get('v');
      const m = url.match(/(?:embed|shorts|watch\/|v\/)([A-Za-z0-9_-]{11})/);
      return m ? m[1] : null;
    } catch { return null; }
  }

  function buildSrc(id) {
    const p = new URLSearchParams({
      autoplay: 1,
      playsinline: 1,
      modestbranding: 1,
      rel: 0,
      // Чтобы точно зациклилось (если нужно): loop=1&playlist=<ID>
      // loop: 1, playlist: id
    });
    return `https://www.youtube-nocookie.com/embed/${id}?${p.toString()}`;
  }

  function openModal() {
    const id = getYouTubeId(btn.dataset.yturl || '');
    if (!id) return;

    const iframe = document.createElement('iframe');
    iframe.src = buildSrc(id);
    iframe.title = 'YouTube video';
    iframe.allow = 'autoplay; encrypted-media; picture-in-picture';
    iframe.allowFullscreen = true;
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    slot.innerHTML = '';
    slot.appendChild(iframe);

    modal.hidden = false;
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    modal.hidden = true;
    slot.innerHTML = ''; // удаляем iframe, чтобы остановить воспроизведение
    document.body.style.overflow = '';
  }

  btn.addEventListener('click', openModal);
  modal.addEventListener('click', (e) => {
    if (e.target.hasAttribute('data-close')) closeModal();
  });
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !modal.hidden) closeModal();
  });
})();
