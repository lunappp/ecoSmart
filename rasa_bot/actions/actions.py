from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import os
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EcoSmart.settings')
django.setup()

from Planes_app.models import Plan, Dinero, Ingreso, Gasto, Objetivo

class ActionGetPlanData(Action):

    def name(self) -> Text:
        return "action_get_plan_data"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        plan_id = tracker.get_slot('plan_id')

        if not plan_id:
            dispatcher.utter_message(text="No tengo información del plan específico. ¿Puedes proporcionarme el ID del plan?")
            return []

        try:
            plan = Plan.objects.get(id=plan_id)
            dinero = Dinero.objects.get(plan=plan)

            total_ingresos = dinero.ingreso_total
            total_gastos = dinero.gasto_total
            balance = total_ingresos - total_gastos

            dispatcher.utter_message(text=f"Información del plan '{plan.nombre}':")
            dispatcher.utter_message(text=f"Total de ingresos: ${total_ingresos}")
            dispatcher.utter_message(text=f"Total de gastos: ${total_gastos}")
            dispatcher.utter_message(text=f"Balance actual: ${balance}")

            return []

        except Plan.DoesNotExist:
            dispatcher.utter_message(text="No encontré un plan con ese ID.")
            return []
        except Exception as e:
            dispatcher.utter_message(text=f"Error al obtener datos del plan: {str(e)}")
            return []

class ActionGiveBudgetAdvice(Action):

    def name(self) -> Text:
        return "action_give_budget_advice"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        plan_id = tracker.get_slot('plan_id')

        if not plan_id:
            dispatcher.utter_message(text="Para darte consejos específicos, necesito saber de qué plan estamos hablando.")
            return []

        try:
            plan = Plan.objects.get(id=plan_id)
            dinero = Dinero.objects.get(plan=plan)

            total_ingresos = dinero.ingreso_total
            total_gastos = dinero.gasto_total

            if total_ingresos > 0:
                porcentaje_gastos = (total_gastos / total_ingresos) * 100

                if porcentaje_gastos > 80:
                    advice = "Tus gastos representan más del 80% de tus ingresos. Considera reducir gastos innecesarios."
                elif porcentaje_gastos > 60:
                    advice = "Tus gastos están en un nivel moderado. Podrías ahorrar más aumentando tus ingresos o reduciendo gastos."
                else:
                    advice = "¡Excelente! Tus gastos están bien controlados. Continúa así."
            else:
                advice = "No tienes ingresos registrados. Comienza agregando tus fuentes de ingresos."

            dispatcher.utter_message(text=advice)
            return []

        except Exception as e:
            dispatcher.utter_message(text=f"Error al analizar presupuesto: {str(e)}")
            return []

class ActionAnalyzeExpenses(Action):

    def name(self) -> Text:
        return "action_analyze_expenses"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        plan_id = tracker.get_slot('plan_id')

        if not plan_id:
            dispatcher.utter_message(text="Necesito el ID del plan para analizar los gastos.")
            return []

        try:
            plan = Plan.objects.get(id=plan_id)
            dinero = Dinero.objects.get(plan=plan)

            gastos_por_categoria = {}
            for gasto in dinero.gastos.all():
                categoria = gasto.tipo_gasto
                if categoria not in gastos_por_categoria:
                    gastos_por_categoria[categoria] = 0
                gastos_por_categoria[categoria] += gasto.cantidad

            if gastos_por_categoria:
                categoria_mayor = max(gastos_por_categoria, key=gastos_por_categoria.get)
                monto_mayor = gastos_por_categoria[categoria_mayor]

                dispatcher.utter_message(text=f"Tu categoría de gastos más alta es '{categoria_mayor}' con ${monto_mayor}")
                dispatcher.utter_message(text="Considera revisar si puedes reducir gastos en esta categoría.")
            else:
                dispatcher.utter_message(text="No tienes gastos registrados en este plan.")

            return []

        except Exception as e:
            dispatcher.utter_message(text=f"Error al analizar gastos: {str(e)}")
            return []

class ActionSuggestSavings(Action):

    def name(self) -> Text:
        return "action_suggest_savings"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        plan_id = tracker.get_slot('plan_id')

        if not plan_id:
            dispatcher.utter_message(text="Para sugerencias personalizadas, necesito el ID del plan.")
            return []

        try:
            plan = Plan.objects.get(id=plan_id)
            dinero = Dinero.objects.get(plan=plan)

            total_ingresos = dinero.ingreso_total
            total_gastos = dinero.gasto_total

            if total_ingresos > 0:
                ahorro_actual = total_ingresos - total_gastos
                porcentaje_ahorro = (ahorro_actual / total_ingresos) * 100

                if porcentaje_ahorro < 20:
                    sugerencia = f"Actualmente ahorras {porcentaje_ahorro:.1f}% de tus ingresos. El objetivo recomendado es 20%. Considera aumentar tus ahorros."
                else:
                    sugerencia = f"¡Excelente! Estás ahorrando {porcentaje_ahorro:.1f}% de tus ingresos, lo cual está por encima del 20% recomendado."
            else:
                sugerencia = "No tienes ingresos registrados. Comienza por registrar tus ingresos para poder calcular ahorros."

            dispatcher.utter_message(text=sugerencia)
            return []

        except Exception as e:
            dispatcher.utter_message(text=f"Error al sugerir ahorros: {str(e)}")
            return []

class ActionInvestmentRecommendations(Action):

    def name(self) -> Text:
        return "action_investment_recommendations"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        plan_id = tracker.get_slot('plan_id')

        if not plan_id:
            dispatcher.utter_message(text="Para recomendaciones de inversión, necesito información de tu plan.")
            return []

        try:
            plan = Plan.objects.get(id=plan_id)
            dinero = Dinero.objects.get(plan=plan)

            total_ingresos = dinero.ingreso_total
            total_gastos = dinero.gasto_total
            balance = total_ingresos - total_gastos

            if balance > 1000:
                recomendacion = "Tienes un buen balance. Considera invertir en fondos indexados o ETFs para diversificar."
            elif balance > 500:
                recomendacion = "Tienes un balance moderado. Comienza con inversiones de bajo riesgo como certificados de depósito."
            elif balance > 0:
                recomendacion = "Tienes un balance positivo pequeño. Enfócate en construir una reserva de emergencia primero."
            else:
                recomendacion = "Tienes un balance negativo. Concéntrate en equilibrar tus ingresos y gastos antes de invertir."

            dispatcher.utter_message(text=recomendacion)
            return []

        except Exception as e:
            dispatcher.utter_message(text=f"Error al generar recomendaciones: {str(e)}")
            return []