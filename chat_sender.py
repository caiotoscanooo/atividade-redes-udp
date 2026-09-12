import socket
import threading

TARGET_IP = "127.0.0.1"
PORT = 5001

# Mensagens que ainda aguardam confirmação
pending_messages = {}

# Mensagens já confirmadas
confirmed_messages = {}

# ID da próxima mensagem
msg_counter = 1

# Evita acesso simultâneo aos dicionários
lock = threading.Lock()


def listen_receipts(sock):
    """
    Recebe confirmações DELIVERED|<ID> em segundo plano.
    """

    while True:
        try:
            data, _ = sock.recvfrom(1024)
            raw = data.decode("utf-8")

            parts = raw.split("|", 1)

            if len(parts) != 2:
                continue

            packet_type, msg_id_text = parts

            if packet_type != "DELIVERED":
                continue

            try:
                msg_id = int(msg_id_text)
            except ValueError:
                continue

            with lock:
                if msg_id in pending_messages:
                    text = pending_messages.pop(msg_id)

                    confirmed_messages[msg_id] = text

                    print(
                        f"\n[✓ Entregue] "
                        f"Mensagem {msg_id}: {text}"
                    )

        except OSError:
            break

        except Exception as error:
            print(f"\n[ERRO] Falha ao receber ACK: {error}")


def show_status():
    """
    Exibe mensagens confirmadas e pendentes.
    """

    with lock:
        pending_copy = dict(pending_messages)
        confirmed_count = len(confirmed_messages)

    print("\n========== STATUS ==========")
    print(f"Confirmadas: {confirmed_count}")
    print(f"Pendentes:   {len(pending_copy)}")

    if pending_copy:
        print("\nMensagens pendentes:")

        for msg_id, text in pending_copy.items():
            print(f"  [ID {msg_id}] {text}")

    else:
        print("\nNenhuma mensagem pendente.")

    print("============================\n")


def resend_pending(sock):
    """
    Reenvia todas as mensagens que ainda estão pendentes.
    """

    with lock:
        messages_to_resend = list(pending_messages.items())

    if not messages_to_resend:
        print("\n[REENVIO] Não existem mensagens pendentes.\n")
        return

    print(
        f"\n[REENVIO] Reenviando "
        f"{len(messages_to_resend)} mensagem(ns)..."
    )

    for msg_id, text in messages_to_resend:
        packet = f"MSG|{msg_id}|{text}"

        sock.sendto(
            packet.encode("utf-8"),
            (TARGET_IP, PORT)
        )

        print(f"[REENVIO] ID {msg_id}: {text}")

    print()


def run_chat_sender():
    global msg_counter

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:

        # Associa o cliente a uma porta UDP local antes de iniciar
        # a thread responsável por receber os ACKs.
        s.bind(("0.0.0.0", 0))

        listener = threading.Thread(
            target=listen_receipts,
            args=(s,),
            daemon=True
        )

        listener.start()

        print("=== Mini Chat UDP ===")
        print("Comandos especiais:")
        print("  /status   -> Mostra mensagens confirmadas e pendentes")
        print("  /reenviar -> Reenvia todas as mensagens pendentes\n")

        while True:
            try:
                user_input = input("Digite uma mensagem: ").strip()

                if not user_input:
                    continue

                if user_input == "/status":
                    show_status()
                    continue

                if user_input == "/reenviar":
                    resend_pending(s)
                    continue

                msg_id = msg_counter

                with lock:
                    pending_messages[msg_id] = user_input

                packet = f"MSG|{msg_id}|{user_input}"

                s.sendto(
                    packet.encode("utf-8"),
                    (TARGET_IP, PORT)
                )

                print(
                    f"[Pendente] Mensagem {msg_id} enviada "
                    f"aguardando confirmação."
                )

                msg_counter += 1

            except KeyboardInterrupt:
                print("\nEncerrando cliente...")
                break


if __name__ == "__main__":
    run_chat_sender()