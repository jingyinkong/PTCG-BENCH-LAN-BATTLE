import { Card, GameState, TrainerCard } from '../types/game';
import { ReplayActionData } from '../types/replay';
import PlayerArea from './PlayerArea';

interface Props {
  state: GameState;
  cardImages: Record<string, string>;
  onCardClick?: (card: Card, imageUrl?: string) => void;
  action?: ReplayActionData | null;
  frameIndex?: number;
}

function playerShortLabel(id: string): string {
  return (id ?? '').toLowerCase().includes('player2') ? 'P2' : 'P1';
}

function cleanEnum(value?: string): string | undefined {
  if (!value) return undefined;
  const raw = value.split('.').pop() ?? value;
  return raw.charAt(0).toUpperCase() + raw.slice(1).toLowerCase();
}

function joinParts(parts: Array<string | undefined | null>): string {
  return parts.filter(Boolean).join(' ');
}

function formatReplayCaption(action: ReplayActionData | null | undefined, frameIndex?: number): string {
  if (!action) return frameIndex === 0 ? 'Replay start.' : 'State update.';

  const source = action.source;
  const target = action.target;
  const position = cleanEnum(action.position);

  switch (action.actionType) {
    case 'AttackAction': {
      const attackName = action.attack?.name;
      const damage = action.attack?.damage;
      return joinParts([
        'Attacks',
        source ? `with ${source}` : undefined,
        attackName ? `using ${attackName}` : undefined,
        target ? `on ${target}` : undefined,
        typeof damage === 'number' ? `for ${damage} damage.` : undefined,
      ]);
    }
    case 'PlayPokemonAction':
      return joinParts(['Plays', source, position ? `to ${position}.` : undefined]);
    case 'EvolvePokemonAction':
      return joinParts(['Evolves', target ?? source, source && target ? `into ${source}.` : undefined]);
    case 'AttachEnergyAction':
      return joinParts(['Attaches', source ?? 'Energy', target ? `to ${target}.` : undefined]);
    case 'RetreatAction':
      return 'Retreats the Active Pokemon.';
    case 'UseAbilityAction':
      return joinParts(['Uses', action.ability ? `${source}'s ${action.ability}.` : source ? `${source}'s ability.` : 'an ability.']);
    case 'UseItemAction':
      return joinParts(['Uses Item', source ? `${source}.` : undefined]);
    case 'UseSupporterAction':
      return joinParts(['Plays Supporter', source ? `${source}.` : undefined]);
    case 'UseToolAction':
      return joinParts(['Attaches Tool', source, target ? `to ${target}.` : undefined]);
    case 'PutStadiumAction':
      return joinParts(['Puts Stadium', source, 'into play.']);
    case 'ChooseCardAction':
      return action.chosen?.length
        ? `Chooses ${action.chosen.join(', ')}.`
        : 'Chooses cards.';
    case 'EffectAction':
      return joinParts(['Resolves an effect', source ? `from ${source}.` : undefined]);
    case 'PassTurn':
      return 'Passes the turn.';
    default:
      return joinParts([
        `${action.actionType.replace('Action', '').replace(/([A-Z])/g, ' $1').trim()}.`,
        source,
        target ? `-> ${target}` : undefined,
      ]);
  }
}

function ReplayCaption({ action, frameIndex }: { action?: ReplayActionData | null; frameIndex?: number }) {
  const caption = formatReplayCaption(action, frameIndex);
  const isP2 = (action?.playerId ?? '').toLowerCase().includes('player2');
  const captionCard = (
    <div className={[
      'absolute left-[62%] right-[84px] -translate-y-1/2',
      isP2 ? 'top-[78%]' : 'top-[30%]',
    ].join(' ')}>
      <div className="max-w-[390px] rounded-lg border border-slate-700/80 bg-slate-950/88 px-5 py-2.5 shadow-xl shadow-slate-950/50 backdrop-blur-sm">
        <div className="flex items-start gap-2.5 text-left">
          <span className={[
            'mt-0.5 flex-shrink-0 rounded px-2.5 py-1 text-[12px] font-mono font-bold leading-none',
            isP2 ? 'bg-amber-500/15 text-amber-300' : 'bg-sky-500/15 text-sky-300',
          ].join(' ')}>
            {action ? playerShortLabel(action.playerId) : 'START'}
          </span>
          <p className="text-[17px] font-semibold leading-snug text-slate-100">
            {caption}
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="pointer-events-none absolute inset-0 z-30 grid grid-rows-[34px_minmax(0,1fr)_24px_minmax(0,1fr)] gap-2">
      <div />
      <div className="relative min-h-0">{isP2 && captionCard}</div>
      <div />
      <div className="relative min-h-0">{!isP2 && captionCard}</div>
    </div>
  );
}

export default function ReplayBoard({ state, cardImages, onCardClick, action, frameIndex }: Props) {
  const stadiumCard = state.stadium && state.stadium.length > 0 ? state.stadium[0] : null;

  const handleStadiumClick = () => {
    if (!stadiumCard || !onCardClick) return;
    const asTrainerCard: TrainerCard = { name: stadiumCard.name, trainerType: 'STADIUM' };
    onCardClick(asTrainerCard, cardImages[stadiumCard.name]);
  };

  return (
    <div
      className="relative grid h-full min-h-0 grid-rows-[34px_minmax(0,1fr)_24px_minmax(0,1fr)] gap-2 rounded-xl overflow-hidden"
      data-testid="replay-board"
    >
      {/* Game info bar */}
      <div className="bg-slate-900 rounded-lg px-4 py-1.5 flex items-center justify-between text-sm border border-slate-800 min-h-0">
        <div className="text-slate-400 text-xs">
          Turn: <span className="text-sky-400 font-mono font-medium uppercase ml-1">{state.turn ?? '—'}</span>
        </div>
        <div className="text-slate-500 text-xs">
          Step: <span className="text-slate-300 font-mono font-medium ml-1">{state.timestep ?? '—'}</span>
        </div>
      </div>

      {/* Player 2 */}
      <PlayerArea player={state.player2} isOpponent playerName="Player 2" cardImages={cardImages} onCardClick={onCardClick} />

      {/* Stadium divider */}
      <div className="flex items-center gap-3 px-2 min-h-0">
        <div className="h-px flex-1 bg-slate-800" />
        <div
          className={[
            'flex items-center gap-2 px-3 py-1 rounded-full border transition-all duration-150',
            stadiumCard
              ? 'border-sky-500/50 bg-sky-950/20 cursor-pointer hover:border-sky-400 hover:bg-sky-950/40'
              : 'border-slate-800 bg-slate-950/40',
          ].join(' ')}
          onClick={stadiumCard ? handleStadiumClick : undefined}
          title={stadiumCard ? `Click to view ${stadiumCard.name}` : undefined}
        >
          <span className="text-[10px] uppercase tracking-widest text-slate-600 font-semibold">Stadium</span>
          {stadiumCard && <span className="text-xs text-sky-400 font-medium">— {stadiumCard.name}</span>}
        </div>
        <div className="h-px flex-1 bg-slate-800" />
      </div>

      {/* Player 1 */}
      <PlayerArea player={state.player1} isOpponent={false} playerName="Player 1" cardImages={cardImages} onCardClick={onCardClick} />

      <ReplayCaption action={action} frameIndex={frameIndex} />
    </div>
  );
}
