from app import create_app
from app.tasks.subscription_maintenance import desativar_ou_notificar_subscricoes
import sys
import traceback

app = create_app()

try:
    with app.app_context():
        print("[✓] Executando manutenção de assinaturas...")
        desativar_ou_notificar_subscricoes()
        print("[✓] Tarefa concluída com sucesso.")
except Exception as e:
    print("[✗] Erro durante execução da manutenção:")
    print(str(e))
    traceback.print_exc(file=sys.stdout)
