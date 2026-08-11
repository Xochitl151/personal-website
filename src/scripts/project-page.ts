const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function slugify(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^\w\u4e00-\u9fff-]/g, '');
}

function initToc(): void {
  const prose = document.querySelector<HTMLElement>('.prose--case');
  const list = document.querySelector<HTMLElement>('[data-toc-list]');
  if (!prose || !list) return;

  const headings = [...prose.querySelectorAll<HTMLHeadingElement>('h2')];
  if (headings.length === 0) {
    list.closest('.project-toc')?.remove();
    return;
  }

  list.innerHTML = '';
  const links: HTMLAnchorElement[] = [];

  headings.forEach((heading, index) => {
    if (!heading.id) {
      heading.id = slugify(heading.textContent ?? '') || `section-${index}`;
    }
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.href = `#${heading.id}`;
    a.textContent = heading.textContent;
    a.addEventListener('click', (e) => {
      e.preventDefault();
      heading.scrollIntoView({ behavior: REDUCED_MOTION ? 'auto' : 'smooth', block: 'start' });
      history.replaceState(null, '', `#${heading.id}`);
    });
    li.append(a);
    list.append(li);
    links.push(a);
  });

  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (!visible?.target.id) return;
      links.forEach((link) => link.classList.toggle('is-active', link.getAttribute('href') === `#${visible.target.id}`));
    },
    { rootMargin: '-20% 0px -70% 0px', threshold: [0, 0.5, 1] },
  );
  headings.forEach((h) => observer.observe(h));
}

function initLightbox(): void {
  const images = document.querySelectorAll<HTMLImageElement>('.prose--case img, .demo img');
  if (images.length === 0) return;

  const overlay = document.createElement('div');
  overlay.className = 'lightbox';
  overlay.innerHTML = `
    <button type="button" class="lightbox__close" aria-label="关闭">×</button>
    <figure class="lightbox__figure">
      <img class="lightbox__img" alt="" />
      <figcaption class="lightbox__caption"></figcaption>
    </figure>
  `;
  document.body.append(overlay);

  const imgEl = overlay.querySelector<HTMLImageElement>('.lightbox__img')!;
  const captionEl = overlay.querySelector<HTMLElement>('.lightbox__caption')!;

  const close = () => {
    overlay.classList.remove('is-open');
    document.body.style.overflow = '';
  };

  overlay.querySelector('.lightbox__close')?.addEventListener('click', close);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) close();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close();
  });

  images.forEach((img) => {
    img.style.cursor = 'zoom-in';
    img.setAttribute('loading', 'lazy');
    img.addEventListener('click', () => {
      imgEl.src = img.src;
      imgEl.alt = img.alt;
      captionEl.textContent = img.alt || '';
      overlay.classList.add('is-open');
      document.body.style.overflow = 'hidden';
    });
  });
}

function initReveal(): void {
  if (REDUCED_MOTION) {
    document.querySelectorAll('.reveal').forEach((el) => el.classList.add('is-visible'));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: '0px 0px -40px 0px' },
  );

  document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));
}

function init(): void {
  initToc();
  initLightbox();
  initReveal();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
