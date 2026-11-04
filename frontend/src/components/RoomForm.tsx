import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { api } from "../api";
import { Modal } from "./Modal";

export function RoomForm({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [capacity, setCapacity] = useState(6);

  const mutation = useMutation({
    mutationFn: () => api.createRoom(name, capacity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rooms"] });
      onClose();
    },
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <Modal title="Nova sala" onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <label>
          Nome
          <input
            required
            maxLength={60}
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Ex.: Aurora"
          />
        </label>
        <label>
          Capacidade (pessoas)
          <input
            required
            type="number"
            min={1}
            max={500}
            value={capacity}
            onChange={(event) => setCapacity(Number(event.target.value))}
          />
        </label>
        {mutation.error && (
          <p className="form-error" role="alert">
            {mutation.error.message}
          </p>
        )}
        <footer className="form-actions">
          <button type="button" className="button" onClick={onClose}>
            Voltar
          </button>
          <button type="submit" className="button primary" disabled={mutation.isPending}>
            {mutation.isPending ? "Criando…" : "Criar sala"}
          </button>
        </footer>
      </form>
    </Modal>
  );
}
