from app import create_app
from app.tasks.populate_daily_analytics import populate_daily_analytics
from app.tasks.subscription_maintenance import desativar_ou_notificar_subscricoes
from app.tasks.populate_demo_analytics import populate_demo_analytics
import sys
import traceback


app = create_app()

try:
    with app.app_context():
        print("[✓] Executando manutenção de assinaturas...")
        desativar_ou_notificar_subscricoes()
        print("[✓] Assinaturas atualizadas com sucesso.")

        print("[✓] Populando KPIs diários...")
        populate_daily_analytics()

        print("[✓] Populando KPIs demo.")
        populate_demo_analytics

        print("[✓] Todas as tarefas concluídas com sucesso.")

except Exception as e:
    print("[✗] Erro durante execução das tarefas agendadas:")
    print(str(e))
    traceback.print_exc(file=sys.stdout)
