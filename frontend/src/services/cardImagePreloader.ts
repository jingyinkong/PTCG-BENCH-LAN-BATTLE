import { Card, GameState } from '../types/game';

const loadedUrls = new Set<string>();
const loadingUrls = new Set<string>();
const failedUrls = new Set<string>();

type PreloadPriority = 'high' | 'low' | 'auto';

type PreloadOptions = {
  maxConcurrent?: number;
  priority?: PreloadPriority;
  idle?: boolean;
};

type ImageWithPriority = HTMLImageElement & {
  fetchPriority?: PreloadPriority;
};

function schedulePreload(work: () => void, idle: boolean) {
  if (!idle) {
    work();
    return;
  }

  const win = window as Window & {
    requestIdleCallback?: (callback: () => void, options?: { timeout: number }) => number;
  };

  if (win.requestIdleCallback) {
    win.requestIdleCallback(work, { timeout: 1500 });
  } else {
    window.setTimeout(work, 0);
  }
}

function loadImage(url: string, priority: PreloadPriority): Promise<void> {
  if (loadedUrls.has(url) || loadingUrls.has(url) || failedUrls.has(url)) {
    return Promise.resolve();
  }

  loadingUrls.add(url);

  return new Promise((resolve) => {
    const image: ImageWithPriority = new Image();
    image.decoding = 'async';
    image.loading = 'eager';
    image.fetchPriority = priority;
    image.onload = () => {
      loadingUrls.delete(url);
      loadedUrls.add(url);
      resolve();
    };
    image.onerror = () => {
      loadingUrls.delete(url);
      failedUrls.add(url);
      resolve();
    };
    image.src = url;
  });
}

export function preloadImageUrls(urls: Array<string | undefined>, options: PreloadOptions = {}) {
  const maxConcurrent = options.maxConcurrent ?? 6;
  const priority = options.priority ?? 'auto';
  const pending = Array.from(new Set(urls.filter((url): url is string => Boolean(url))))
    .filter((url) => !loadedUrls.has(url) && !loadingUrls.has(url) && !failedUrls.has(url));

  if (pending.length === 0) return;

  schedulePreload(() => {
    let index = 0;
    let active = 0;

    const runNext = () => {
      while (active < maxConcurrent && index < pending.length) {
        const url = pending[index];
        index += 1;
        active += 1;
        loadImage(url, priority).finally(() => {
          active -= 1;
          runNext();
        });
      }
    };

    runNext();
  }, options.idle ?? true);
}

function addCardName(names: Set<string>, card: Card | null | undefined) {
  if (card?.name) names.add(card.name);
}

function addCards(names: Set<string>, cards: Card[] | undefined) {
  cards?.forEach((card) => addCardName(names, card));
}

export function getCardNamesFromState(state: GameState | null | undefined): string[] {
  if (!state) return [];

  const names = new Set<string>();

  state.stadium.forEach((stadium) => names.add(stadium.name));

  for (const player of [state.player1, state.player2]) {
    addCards(names, player.active);
    addCards(names, player.bench);
    addCards(names, player.hand);
    addCards(names, player.discard);
    addCards(names, player.prize);
    addCards(names, player.deck);
    addCards(names, player.lostZone);
  }

  return Array.from(names);
}

export function preloadCardImagesForState(state: GameState | null | undefined, cardImages: Record<string, string>) {
  const urls = getCardNamesFromState(state).map((name) => cardImages[name]);
  preloadImageUrls(urls, { maxConcurrent: 8, priority: 'low', idle: true });
}

export function preloadCardImagesByName(cardNames: string[], cardImages: Record<string, string>) {
  const urls = cardNames.map((name) => cardImages[name]);
  preloadImageUrls(urls, { maxConcurrent: 8, priority: 'low', idle: true });
}
