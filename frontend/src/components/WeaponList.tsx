import { useCallback } from "react";
import type { Weapon } from "../types/game";
import { addWeapon, removeWeapon } from "../api/endpoints";
import EditableItemList from "./EditableItemList";

interface WeaponListProps {
  weapons: Weapon[];
  gameCode: string;
  token: string;
  currentPlayerId: string;
  hostId: string;
  onMutate: () => void;
}

const weaponIcon = (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 20 20"
    fill="currentColor"
    className="w-4 h-4"
    aria-hidden="true"
  >
    <path
      fillRule="evenodd"
      d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.534-.398-2.654A1 1 0 005.05 6.05 6.981 6.981 0 003 11a7 7 0 1011.95-4.95c-.592-.591-.98-.985-1.348-1.467-.363-.476-.724-1.063-1.207-2.03zM12.12 15.12A3 3 0 017 13s.879.5 2.5.5c0-1 .5-2 1-3 .5 1.5 1 2 1 3a3 3 0 01-.38 1.62z"
      clipRule="evenodd"
    />
  </svg>
);

export default function WeaponList({
  weapons,
  gameCode,
  token,
  currentPlayerId,
  hostId,
  onMutate,
}: WeaponListProps) {
  const handleAdd = useCallback(
    async (name: string) => {
      await addWeapon(gameCode, name, token);
      onMutate();
    },
    [gameCode, token, onMutate],
  );

  const handleRemove = useCallback(
    async (id: string) => {
      await removeWeapon(gameCode, id, token);
      onMutate();
    },
    [gameCode, token, onMutate],
  );

  return (
    <EditableItemList
      items={weapons}
      currentPlayerId={currentPlayerId}
      hostId={hostId}
      label="Weapons"
      singularLabel="weapon"
      emptyMessage="No weapons yet. Add items from around the house!"
      placeholder="Add a weapon..."
      icon={weaponIcon}
      onAdd={handleAdd}
      onRemove={handleRemove}
    />
  );
}
