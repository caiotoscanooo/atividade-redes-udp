import random
import socket

HOST = "0.0.0.0"
PORT = 5001
DROP_RATE = 0.4  # 40% de perda simulada no canal


def run_chat_receiver():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))

        print(
            f"[Chat Server] Online na porta {PORT} "
            f"(Drop Rate: {DROP_RATE * 100:.0f}%)..."
        )

        while True:
            data, addr = s.recvfrom(1024)

            # Simulação de descarte de pacote
            if random.random() < DROP_RATE:
                print("[CANAL] Pacote descartado artificialmente!")
                continue

            try:
                raw_message = data.decode("utf-8")

                # Formato esperado: MSG|<ID>|<CONTEUDO>
                parts = raw_message.split("|", 2)

                if len(parts) != 3:
                    print(f"[ERRO] Pacote inválido recebido: {raw_message}")
                    continue

                msg_type, msg_id, text = parts

                if msg_type != "MSG":
                    print(f"[ERRO] Tipo de pacote desconhecido: {msg_type}")
                    continue

                print(f"[MSG {msg_id}] {text}")

                # Confirmação em nível de aplicação
                receipt = f"DELIVERED|{msg_id}"

                s.sendto(receipt.encode("utf-8"), addr)

                print(f"[ACK] DELIVERED|{msg_id} enviado.")

            except UnicodeDecodeError:
                print("[ERRO] Não foi possível decodificar o pacote recebido.")

            except Exception as error:
                print(f"[ERRO] Falha ao processar pacote: {error}")


if __name__ == "__main__":
    run_chat_receiver()