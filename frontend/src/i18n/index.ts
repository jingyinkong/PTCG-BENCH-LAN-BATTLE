import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import zhCommon from './resources/zh-CN/common.json';
import zhGame from './resources/zh-CN/game.json';
import zhLobby from './resources/zh-CN/lobby.json';
import zhAuth from './resources/zh-CN/auth.json';
import zhDeck from './resources/zh-CN/deck.json';
import zhLeaderboard from './resources/zh-CN/leaderboard.json';

import enCommon from './resources/en-US/common.json';
import enGame from './resources/en-US/game.json';
import enLobby from './resources/en-US/lobby.json';
import enAuth from './resources/en-US/auth.json';
import enDeck from './resources/en-US/deck.json';
import enLeaderboard from './resources/en-US/leaderboard.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      'zh-CN': {
        common: zhCommon,
        game: zhGame,
        lobby: zhLobby,
        auth: zhAuth,
        deck: zhDeck,
        leaderboard: zhLeaderboard,
      },
      'en-US': {
        common: enCommon,
        game: enGame,
        lobby: enLobby,
        auth: enAuth,
        deck: enDeck,
        leaderboard: enLeaderboard,
      },
    },
    fallbackLng: 'zh-CN',
    defaultNS: 'common',
    interpolation: { escapeValue: false },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },
  });

export default i18n;
