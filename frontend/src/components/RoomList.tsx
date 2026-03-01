import { useCallback } from "react";
import type { Room } from "../types/game";
import { addRoom, removeRoom } from "../api/endpoints";
import EditableItemList from "./EditableItemList";

interface RoomListProps {
  rooms: Room[];
  gameCode: string;
  token: string;
  onMutate: () => void;
}

const roomIcon = (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 20 20"
    fill="currentColor"
    className="w-4 h-4"
    aria-hidden="true"
  >
    <path
      fillRule="evenodd"
      d="M9.293 2.293a1 1 0 011.414 0l7 7A1 1 0 0117 11h-1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-3a1 1 0 00-1-1H9a1 1 0 00-1 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-6H3a1 1 0 01-.707-1.707l7-7z"
      clipRule="evenodd"
    />
  </svg>
);

export default function RoomList({
  rooms,
  gameCode,
  token,
  onMutate,
}: RoomListProps) {
  const handleAdd = useCallback(
    async (name: string) => {
      await addRoom(gameCode, name, token);
      onMutate();
    },
    [gameCode, token, onMutate],
  );

  const handleRemove = useCallback(
    async (id: string) => {
      await removeRoom(gameCode, id, token);
      onMutate();
    },
    [gameCode, token, onMutate],
  );

  return (
    <EditableItemList
      items={rooms}
      label="Rooms"
      singularLabel="room"
      emptyMessage="No rooms yet. Add rooms from your Airbnb!"
      placeholder="Add a room..."
      icon={roomIcon}
      onAdd={handleAdd}
      onRemove={handleRemove}
    />
  );
}
