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
/****************************** */
/****************************** */
/****************************** */
/****************************** */
(function() {
  // ===== helpers =====
  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/i;
  function setError(container, message) {
    container.classList.add('error');
    const err = container.querySelector('.form__error');
    if (err) err.textContent = message || '';
  }
  function clearError(container) {
    container.classList.remove('error');
    const err = container.querySelector('.form__error');
    if (err) err.textContent = '';
  }

  // ===== custom select =====
  document.querySelectorAll('.custom-select').forEach(select => {
    const trigger = select.querySelector('.custom-select__trigger');
    const dropdown = select.querySelector('.custom-select__dropdown');
    const labelEl = select.querySelector('.custom-select__label');
    const hiddenInputName = select.dataset.name || 'custom';
    const placeholder = select.dataset.placeholder || 'Select...';

    // найти связанный скрытый input
    let hidden = document.getElementById(hiddenInputName);
    if (!hidden) {
      hidden = document.createElement('input');
      hidden.type = 'hidden';
      hidden.name = hiddenInputName;
      hidden.id = hiddenInputName;
      select.parentElement.appendChild(hidden);
    }

    // открыть/закрыть
    function open() {
      select.classList.add('open');
      trigger.setAttribute('aria-expanded', 'true');
      dropdown.focus({ preventScroll: true });
    }
    function close() {
      select.classList.remove('open');
      trigger.setAttribute('aria-expanded', 'false');
    }

    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      select.classList.contains('open') ? close() : open();
    });

    // выбор пункта
    dropdown.querySelectorAll('.custom-select__option').forEach(opt => {
      opt.addEventListener('click', () => {
        dropdown.querySelectorAll('.custom-select__option').forEach(o => o.removeAttribute('aria-selected'));
        opt.setAttribute('aria-selected', 'true');
        const value = opt.dataset.value || opt.textContent.trim();
        labelEl.textContent = opt.textContent.trim();
        hidden.value = value;
        close();
        // убрать ошибку при выборе
        clearError(select);
      });
    });

    // клик вне
    document.addEventListener('click', (e) => {
      if (!select.contains(e.target)) close();
    });

    // esc
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') close();
    });

    // init label
    labelEl.textContent = placeholder;
  });

  // ===== validation & submit =====
  const form = document.querySelector('.footer__form');
  if (!form) return;

  form.addEventListener('submit', function(e) {
    let valid = true;

    // name
    const nameEl = form.querySelector('input[type="text"]');
    const nameWrap = nameEl.closest('.form__element') || nameEl.parentElement;
    clearError(nameWrap);
    if (!nameEl.value.trim()) {
      setError(nameWrap, 'Please enter your name');
      valid = false;
    }

    // email
    const emailEl = form.querySelector('input[type="email"]');
    const emailWrap = emailEl.closest('.form__element') || emailEl.parentElement;
    clearError(emailWrap);
    if (!emailRe.test(emailEl.value.trim())) {
      setError(emailWrap, 'Please enter a valid email');
      valid = false;
    }

    // custom select (hidden input)
    const selectWrap = form.querySelector('.custom-select')?.closest('.form__element');
    const hiddenSelect = form.querySelector('input[type="hidden"][name="contact_reason"]');
    if (selectWrap && hiddenSelect) {
      clearError(selectWrap);
      if (!hiddenSelect.value) {
        setError(selectWrap.querySelector('.custom-select') || selectWrap, 'Please choose an option');
        selectWrap.classList.add('error');
        valid = false;
      }
    }

    // phone (минимальная проверка)
    const phoneEl = form.querySelector('input[type="number"]');
    const phoneWrap = phoneEl?.closest('.form__element') || phoneEl?.parentElement;
    if (phoneEl && phoneWrap) {
      clearError(phoneWrap);
      const digits = (phoneEl.value || '').replace(/\D/g, '');
      if (digits.length < 7) {
        setError(phoneWrap, 'Please enter a valid phone');
        valid = false;
      }
    }

    // message
    const msgEl = form.querySelector('textarea');
    const msgWrap = msgEl?.closest('.form__elements') || msgEl?.parentElement;
    if (msgEl && msgWrap) {
      // добавим контейнер ошибки, если нужно
      let err = msgWrap.querySelector('.form__error');
      if (!err) {
        err = document.createElement('div');
        err.className = 'form__error';
        msgWrap.appendChild(err);
      }
      msgEl.classList.remove('error');
      err.textContent = '';
      if (!msgEl.value.trim()) {
        msgEl.classList.add('error');
        err.textContent = 'Please enter your message';
        valid = false;
      }
    }

    if (!valid) {
      e.preventDefault();
      return;
    }

    // пока бэка нет — просто покажем alert и заблокируем реальную отправку
    e.preventDefault();
    alert('Form is valid. Next step: wire up SMTP in Django view.');
    // когда подключим Django, удалим e.preventDefault() и дадим реальный action у формы
  });
})();

