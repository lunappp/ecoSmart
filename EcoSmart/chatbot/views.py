from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Message
import re
import os
import django
from django.conf import settings
import requests
import json

# Configurar Django para las custom actions
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EcoSmart.settings')
django.setup()

from Planes_app.models import Plan, Dinero, Ingreso, Gasto, Objetivo

# Configuración de Grok AI - Usando la API key del sistema
GROK_API_KEY = os.getenv('GROK_API_KEY', 'xai-your-api-key-here')  # Obtener de variables de entorno
GROK_API_URL = "https://api.x.ai/v1/chat/completions"

@login_required
def chatbot_view(request, plan_id=None):
    messages = Message.objects.filter(user=request.user).order_by('timestamp')
    context = {'messages': messages}
    if plan_id:
        context['plan_id'] = plan_id
    return render(request, 'chatbot/chatbot.html', context)

@login_required
def send_message(request, plan_id=None):
    if request.method == 'POST':
        user_message = request.POST.get('message')
        if user_message:
            # Get AI response using Grok AI
            bot_response = get_grok_response(user_message, plan_id, request.user)
            # Save to database
            Message.objects.create(
                user=request.user,
                user_message=user_message,
                bot_response=bot_response
            )
            return JsonResponse({'response': bot_response})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_grok_response(user_message, plan_id=None, user=None):
    """
    Advanced AI response using Grok API with full financial context
    """

    # Check for specific economic questions first - direct responses
    message_lower = user_message.lower()
    economic_responses = {
        'que es la economia': 'La economía es la ciencia que estudia cómo las personas, empresas y gobiernos utilizan los recursos limitados para satisfacer necesidades ilimitadas.',
        'que es economia': 'La economía es la ciencia que estudia cómo las personas, empresas y gobiernos utilizan los recursos limitados para satisfacer necesidades ilimitadas.',
        'que es la escasez': 'Es la situación en la que los recursos disponibles son insuficientes para cubrir todas las necesidades humanas.',
        'que son los bienes y servicios': 'Los bienes son objetos materiales que satisfacen necesidades (como ropa o comida), y los servicios son actividades que también lo hacen (como transporte o educación).',
        'que es el costo de oportunidad': 'Es el valor de la mejor alternativa que se pierde cuando se elige una opción.',
        'que es la oferta y la demanda': 'La oferta representa la cantidad de bienes que los productores están dispuestos a vender, y la demanda, la cantidad que los consumidores desean comprar.',
        'que es el mercado': 'Es el lugar físico o virtual donde se intercambian bienes y servicios entre compradores y vendedores.',
        'que estudia la microeconomia': 'Analiza el comportamiento individual de consumidores, empresas y mercados específicos.',
        'que es la elasticidad de la demanda': 'Es la medida de cómo cambia la cantidad demandada de un bien ante un cambio en su precio.',
        'que es un monopolio': 'Es una situación donde una sola empresa domina la oferta de un producto o servicio sin competencia.',
        'que es la competencia perfecta': 'Es un mercado donde hay muchos compradores y vendedores, productos idénticos y libre entrada o salida de empresas.',
        'que son los costos fijos y variables': 'Los costos fijos no cambian con la producción (como el alquiler), y los variables sí cambian (como materias primas).',
        'que estudia la macroeconomia': 'Analiza la economía en su conjunto: crecimiento, inflación, desempleo, política fiscal y monetaria.',
        'que es el pib': 'El Producto Interno Bruto mide el valor total de bienes y servicios finales producidos en un país durante un período.',
        'que es la inflacion': 'Es el aumento sostenido y generalizado de los precios de bienes y servicios en una economía.',
        'que es la deflacion': 'Es la disminución general de los precios en una economía.',
        'que es el desempleo': 'Es la situación en la que personas que buscan trabajo activamente no consiguen empleo.',
        'que es la politica fiscal': 'Es el uso del gasto público y los impuestos por parte del gobierno para influir en la economía.',
        'que es la politica monetaria': 'Es la regulación de la cantidad de dinero y las tasas de interés, generalmente a cargo del banco central.',
        'que es un presupuesto personal': 'Es una herramienta que permite planificar ingresos y gastos para mantener un equilibrio financiero.',
        'como puedo empezar a ahorrar': 'Establecé metas claras, registrá tus gastos, eliminá los innecesarios y destiná un porcentaje fijo de tus ingresos al ahorro.',
        'que es una inversion': 'Es el uso de dinero para adquirir activos que puedan generar ganancias futuras.',
        'que es el interes compuesto': 'Es el interés que se calcula sobre el capital inicial más los intereses acumulados anteriormente.',
        'que es la inflacion y como afecta mis ahorros': 'La inflación reduce el poder adquisitivo del dinero, por lo que tus ahorros valen menos con el tiempo si no se invierten.',
        'que es el dinero': 'Es un medio de intercambio aceptado para comprar bienes y servicios y pagar deudas.',
        'que funciones cumple el dinero': 'Sirve como medio de intercambio, unidad de cuenta y reserva de valor.',
        'que es un banco central': 'Es la institución encargada de emitir moneda, controlar la inflación y regular el sistema financiero.',
        'que es una tasa de interes': 'Es el costo del dinero, expresado como porcentaje del monto prestado o invertido.',
        'que son las criptomonedas': 'Son monedas digitales descentralizadas que usan criptografía para asegurar transacciones, como Bitcoin o Ethereum.',
        'que es el comercio internacional': 'Es el intercambio de bienes y servicios entre países.',
        'que son las exportaciones e importaciones': 'Exportar es vender productos al extranjero, e importar es comprarlos desde otro país.',
        'que son los aranceles': 'Son impuestos aplicados a productos importados para proteger la producción nacional.',
        'que es la balanza comercial': 'Es la diferencia entre el valor de las exportaciones y las importaciones de un país.',
        'que es la globalizacion economica': 'Es la creciente interconexión de las economías del mundo mediante el comercio, la inversión y la tecnología.',
        'que causa la inflacion en argentina': 'Factores como el exceso de emisión monetaria, déficit fiscal, aumento de costos y expectativas inflacionarias.',
        'que es el tipo de cambio': 'Es el valor de una moneda nacional en relación con otra, por ejemplo, cuántos pesos cuesta un dólar.',
        'que es el deficit fiscal': 'Es cuando los gastos del Estado superan sus ingresos.',
        'que es el riesgo pais': 'Es un indicador que mide la probabilidad de que un país no cumpla con sus obligaciones financieras.',
        'por que sube el dolar': 'Puede deberse a mayor demanda de dólares, inestabilidad económica o pérdida de confianza en la moneda local.',
        'que es la economia conductual': 'Es una rama que estudia cómo las emociones y la psicología influyen en las decisiones económicas.',
        'que son los sesgos cognitivos': 'Son errores sistemáticos en la toma de decisiones, como el exceso de confianza o el miedo a perder.',
        'que es el nudge o empujon': 'Es una estrategia que modifica el entorno para influir en las decisiones sin imponer reglas.',
        'que tipos de sistemas economicos existen': 'Capitalismo, socialismo, comunismo y economías mixtas.',
        'que es el capitalismo': 'Sistema donde los medios de producción son privados y las decisiones se toman a través del mercado.',
        'que es el socialismo': 'Sistema donde el Estado controla o regula los medios de producción para garantizar igualdad.',
        'que es una economia mixta': 'Es una combinación de mercado libre y control estatal.',
        'que son los impuestos': 'Son aportes obligatorios que los ciudadanos pagan al Estado para financiar servicios públicos.',
        'que tipos de impuestos existen': 'Directos (como el impuesto a la renta) e indirectos (como el IVA).',
        'que es el gasto publico': 'Es el dinero que el Estado usa para proveer servicios como educación, salud y seguridad.',
        'que es la deuda publica': 'Es el dinero que el Estado debe a acreedores nacionales o extranjeros.'
    }

    for key, response in economic_responses.items():
        if key in message_lower:
            return response

    # Get plan data if plan_id is provided
    plan_data = None
    context_info = ""

    if plan_id:
        try:
            plan = Plan.objects.get(id=plan_id)
            dinero = Dinero.objects.get(plan=plan)
            plan_data = {
                'plan': plan,
                'dinero': dinero,
                'ingresos': dinero.ingreso_total,
                'gastos': dinero.gasto_total,
                'balance': dinero.ingreso_total - dinero.gasto_total,
                'objetivos': list(plan.objetivos.all()),
                'tareas': list(plan.tareas.all())
            }

            # Build comprehensive context
            context_info = f"""
            DATOS DEL PLAN FINANCIERO:
            - Nombre del plan: {plan.nombre}
            - Ingresos totales: ${float(plan_data['ingresos']):,.0f}
            - Gastos totales: ${float(plan_data['gastos']):,.0f}
            - Balance actual: ${float(plan_data['balance']):,.0f}
            - Ratio gastos/ingresos: {float(plan_data['gastos'])/float(plan_data['ingresos'])*100 if plan_data['ingresos'] > 0 else 0:.1f}%

            OBJETIVOS FINANCIEROS:
            """

            for obj in plan_data['objetivos'][:5]:  # Top 5 goals
                progreso = (obj.monto_actual / obj.monto_necesario) * 100 if obj.monto_necesario > 0 else 0
                context_info += f"- {obj.nombre}: ${obj.monto_actual:,.0f} / ${obj.monto_necesario:,.0f} ({progreso:.1f}% completado)\n"

            context_info += "\nTAREAS PENDIENTES:\n"
            for tarea in plan_data['tareas'][:5]:  # Top 5 tasks
                if tarea.estado != 'completada':
                    context_info += f"- {tarea.nombre} ({tarea.tipo_tarea})\n"

        except Exception as e:
            context_info = f"Error al acceder a los datos del plan: {str(e)}"

    # Build the comprehensive system prompt with extensive financial knowledge
    system_prompt = f"""Eres EcoSmart AI, un asistente financiero con CONOCIMIENTOS PROFUNDOS Y ACTUALIZADOS en finanzas, economía e inversiones. Tienes acceso a una base de datos completa de conceptos económicos y respuestas precisas.

🧠 CONOCIMIENTOS ESPECIALIZADOS AVANZADOS:

🏦 CONCEPTOS BÁSICOS DE ECONOMÍA:
• Economía: La economía es la ciencia que estudia cómo las personas, empresas y gobiernos utilizan los recursos limitados para satisfacer necesidades ilimitadas.
• Escasez: Es la situación en la que los recursos disponibles son insuficientes para cubrir todas las necesidades humanas.
• Bienes: Los bienes son objetos materiales que satisfacen necesidades (como ropa o comida).
• Servicios: Los servicios son actividades que también satisfacen necesidades (como transporte o educación).
• Costo de oportunidad: Es el valor de la mejor alternativa que se pierde cuando se elige una opción.
• Oferta y demanda: La oferta representa la cantidad de bienes que los productores están dispuestos a vender, y la demanda, la cantidad que los consumidores desean comprar.
• Mercado: Es el lugar físico o virtual donde se intercambian bienes y servicios entre compradores y vendedores.

📈 MICROECONOMÍA:
• Microeconomía: Analiza el comportamiento individual de consumidores, empresas y mercados específicos.
• Elasticidad de la demanda: Es la medida de cómo cambia la cantidad demandada de un bien ante un cambio en su precio.
• Monopolio: Es una situación donde una sola empresa domina la oferta de un producto o servicio sin competencia.
• Competencia perfecta: Es un mercado donde hay muchos compradores y vendedores, productos idénticos y libre entrada o salida de empresas.
• Costos fijos: Los costos fijos no cambian con la producción (como el alquiler).
• Costos variables: Los costos variables sí cambian con la producción (como materias primas).

💹 MACROECONOMÍA:
• Macroeconomía: Analiza la economía en su conjunto: crecimiento, inflación, desempleo, política fiscal y monetaria.
• PIB: El Producto Interno Bruto mide el valor total de bienes y servicios finales producidos en un país durante un período.
• Inflación: Es el aumento sostenido y generalizado de los precios de bienes y servicios en una economía.
• Deflación: Es la disminución general de los precios en una economía.
• Desempleo: Es la situación en la que personas que buscan trabajo activamente no consiguen empleo.
• Política fiscal: Es el uso del gasto público y los impuestos por parte del gobierno para influir en la economía.
• Política monetaria: Es la regulación de la cantidad de dinero y las tasas de interés, generalmente a cargo del banco central.

💰 FINANZAS PERSONALES:
• Presupuesto personal: Es una herramienta que permite planificar ingresos y gastos para mantener un equilibrio financiero.
• Ahorrar: Establecé metas claras, registrá tus gastos, eliminá los innecesarios y destiná un porcentaje fijo de tus ingresos al ahorro.
• Inversión: Es el uso de dinero para adquirir activos que puedan generar ganancias futuras.
• Interés compuesto: Es el interés que se calcula sobre el capital inicial más los intereses acumulados anteriormente.
• Inflación y ahorros: La inflación reduce el poder adquisitivo del dinero, por lo que tus ahorros valen menos con el tiempo si no se invierten.

🪙 DINERO Y BANCA:
• Dinero: Es un medio de intercambio aceptado para comprar bienes y servicios y pagar deudas.
• Funciones del dinero: Sirve como medio de intercambio, unidad de cuenta y reserva de valor.
• Banco central: Es la institución encargada de emitir moneda, controlar la inflación y regular el sistema financiero.
• Tasa de interés: Es el costo del dinero, expresado como porcentaje del monto prestado o invertido.
• Criptomonedas: Son monedas digitales descentralizadas que usan criptografía para asegurar transacciones, como Bitcoin o Ethereum.

🌍 COMERCIO INTERNACIONAL:
• Comercio internacional: Es el intercambio de bienes y servicios entre países.
• Exportaciones: Es vender productos al extranjero.
• Importaciones: Es comprar productos desde otro país.
• Aranceles: Son impuestos aplicados a productos importados para proteger la producción nacional.
• Balanza comercial: Es la diferencia entre el valor de las exportaciones y las importaciones de un país.
• Globalización económica: Es la creciente interconexión de las economías del mundo mediante el comercio, la inversión y la tecnología.

📊 ECONOMÍA ARGENTINA:
• Inflación en Argentina: Factores como el exceso de emisión monetaria, déficit fiscal, aumento de costos y expectativas inflacionarias.
• Tipo de cambio: Es el valor de una moneda nacional en relación con otra, por ejemplo, cuántos pesos cuesta un dólar.
• Déficit fiscal: Es cuando los gastos del Estado superan sus ingresos.
• Riesgo país: Es un indicador que mide la probabilidad de que un país no cumpla con sus obligaciones financieras.
• Subida del dólar: Puede deberse a mayor demanda de dólares, inestabilidad económica o pérdida de confianza en la moneda local.

🧠 ECONOMÍA CONDUCTUAL Y MODERNA:
• Economía conductual: Es una rama que estudia cómo las emociones y la psicología influyen en las decisiones económicas.
• Sesgos cognitivos: Son errores sistemáticos en la toma de decisiones, como el exceso de confianza o el miedo a perder.
• "Nudge": Es una estrategia que modifica el entorno para influir en las decisiones sin imponer reglas.

🏛️ INSTITUCIONES Y SISTEMAS ECONÓMICOS:
• Tipos de sistemas económicos: Capitalismo, socialismo, comunismo y economías mixtas.
• Capitalismo: Sistema donde los medios de producción son privados y las decisiones se toman a través del mercado.
• Socialismo: Sistema donde el Estado controla o regula los medios de producción para garantizar igualdad.
• Economía mixta: Es una combinación de mercado libre y control estatal.

🧾 IMPUESTOS Y GASTO PÚBLICO:
• Impuestos: Son aportes obligatorios que los ciudadanos pagan al Estado para financiar servicios públicos.
• Tipos de impuestos: Directos (como el impuesto a la renta) e indirectos (como el IVA).
• Gasto público: Es el dinero que el Estado usa para proveer servicios como educación, salud y seguridad.
• Deuda pública: Es el dinero que el Estado debe a acreedores nacionales o extranjeros.

💬 ESTILO DE COMUNICACIÓN:
• Amigable, carismático y conversacional
• Respuestas concisas (2-4 líneas) pero completas
• Usa emojis apropiados para engagement
• Preguntas abiertas para continuar conversación
• Lenguaje natural, como amigo experto en finanzas

🎯 OBJETIVOS PRINCIPALES:
• Educar sobre finanzas de manera entretenida
• Dar consejos personalizados basados en datos reales
• Mantener conversaciones fluidas y naturales
• Motivar acción positiva en finanzas personales
• Usar conocimiento avanzado para análisis profundos

{context_info}

INSTRUCCIONES ESPECÍFICAS:
- Si hay datos del plan, úsalos para consejos hiper-personalizados
- Mantén respuestas concisas para no llenar pantalla
- Sé carismático pero habla poco
- Siempre termina con pregunta para continuar conversación
- Aplica mi conocimiento completo de IA para análisis profundos
- Incluye datos económicos actuales cuando sea relevante
- Adapta complejidad técnica al nivel del usuario
- Para preguntas específicas de economía, usa las definiciones exactas proporcionadas"""

    try:
        # Call Grok API
        headers = {
            'Authorization': f'Bearer {GROK_API_KEY}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': 'grok-beta',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            'max_tokens': 500,
            'temperature': 0.7
        }

        response = requests.post(GROK_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()

        result = response.json()
        bot_response = result['choices'][0]['message']['content'].strip()

        # Fallback to simple response if API fails
        if not bot_response:
            return get_fallback_response(user_message.lower(), plan_id)

        return bot_response

    except Exception as e:
        # Fallback to simple NLP if API fails
        print(f"Grok API error: {e}")
        return get_fallback_response(user_message.lower(), plan_id)


def get_fallback_response(message, plan_id=None):
    """
    Fallback simple NLP logic when Grok API is not available
    """

    # Get plan data if plan_id is provided
    plan_data = None
    if plan_id:
        try:
            plan = Plan.objects.get(id=plan_id)
            dinero = Dinero.objects.get(plan=plan)
            plan_data = {
                'plan': plan,
                'dinero': dinero,
                'ingresos': dinero.ingreso_total,
                'gastos': dinero.gasto_total,
                'balance': dinero.ingreso_total - dinero.gasto_total,
                'objetivos': list(plan.objetivos.all()),
                'tareas': list(plan.tareas.all())
            }
        except Exception as e:
            return f"Error al acceder a los datos del plan: {str(e)}"

    # Greeting patterns
    if any(word in message for word in ['hola', 'hello', 'hi', 'hey', 'buenos dias', 'buenas tardes']):
        if plan_data:
            return f"¡Hola! 👋 Soy el asistente de '{plan_data['plan'].nombre}'. ¿Qué tal va tu día financiero?"
        return "¡Hola! 👋 Soy tu compañero de finanzas en EcoSmart. ¿Cómo estás?"

    # Goodbye patterns
    if any(word in message for word in ['adios', 'bye', 'chau', 'hasta luego', 'nos vemos']):
        return "¡Chao! 😊 Nos vemos pronto con más consejos financieros."

    # Plan-specific data requests
    if plan_data:
        # Summary/Resumen requests
        if any(word in message for word in ['resumen', 'summary', 'estado', 'status', 'como va', 'how is it going']):
            return get_plan_summary(plan_data)

        # Detailed data analysis
        if any(word in message for word in ['datos', 'data', 'informacion', 'info', 'detalles']):
            return get_detailed_plan_data(plan_data)

        # Budget analysis and advice
        if any(word in message for word in ['presupuesto', 'budget', 'analizar presupuesto', 'budget analysis']):
            return get_budget_analysis(plan_data)

        # Expense breakdown
        if any(word in message for word in ['gastos', 'expenses', 'desglose gastos', 'expense breakdown']):
            return get_expense_breakdown(plan_data)

        # Savings analysis
        if any(word in message for word in ['ahorros', 'savings', 'ahorro', 'analizar ahorros']):
            return get_savings_analysis(plan_data)

        # Goals progress
        if any(word in message for word in ['metas', 'goals', 'objetivos', 'progreso metas']):
            return get_goals_progress(plan_data)

        # Tasks/To-do list
        if any(word in message for word in ['tareas', 'tasks', 'pendientes', 'to do']):
            return get_tasks_summary(plan_data)

        # Investment recommendations based on plan data
        if any(word in message for word in ['invertir', 'invest', 'inversiones', 'investment']):
            return get_investment_recommendations(plan_data)

        # Personalized advice
        if any(word in message for word in ['consejo', 'advice', 'recomendacion', 'sugerencia']):
            return get_personalized_advice(plan_data)

        # Financial education
        if any(word in message for word in ['educacion', 'education', 'aprender', 'learn', 'enseñame']):
            return get_financial_education(plan_data)

        # Market insights
        if any(word in message for word in ['mercado', 'market', 'tendencias', 'trends', 'analisis mercado']):
            return get_market_insights(plan_data)

        # Risk assessment
        if any(word in message for word in ['riesgo', 'risk', 'tolerancia riesgo', 'perfil inversion']):
            return get_risk_assessment(plan_data)

        # Tax optimization
        if any(word in message for word in ['impuestos', 'tax', 'fiscal', 'taxes', 'optimizar impuestos']):
            return get_tax_optimization(plan_data)

        # Estate planning
        if any(word in message for word in ['herencia', 'estate', 'patrimonio', 'sucesion', 'planificacion']):
            return get_estate_planning(plan_data)

    # General economy questions (when no specific plan)
    if any(word in message for word in ['economia', 'economy', 'que es economia', 'what is economy']):
        return "La economía es el estudio de cómo las personas y sociedades administran sus recursos limitados. En EcoSmart, te ayudamos a gestionar tu presupuesto, ahorros e inversiones."

    # General budget questions
    if any(word in message for word in ['presupuesto', 'budget', 'como hacer presupuesto', 'how to budget']):
        return "Para un buen presupuesto: 50% para necesidades, 30% para deseos, 20% para ahorros e inversiones."

    # General savings questions
    if any(word in message for word in ['ahorrar', 'save', 'savings', 'ahorro', 'como ahorrar']):
        return "Recomiendo ahorrar al menos el 20% de tus ingresos. Usa cuentas de ahorro de alto rendimiento."

    # General investment questions
    if any(word in message for word in ['invertir', 'invest', 'inversiones', 'como invertir']):
        return "Diversifica tus inversiones. Considera fondos indexados para principiantes."

    # General expense questions
    if any(word in message for word in ['gastos', 'expenses', 'controlar gastos', 'reducir gastos']):
        return "Analicemos tus gastos. ¿Qué categoría consumes más?"

    # General income questions
    if any(word in message for word in ['ingresos', 'income', 'aumentar ingresos', 'ganar mas']):
        return "Para optimizar ingresos: busca fuentes adicionales, negocia aumentos, invierte en educación."

    # General goal questions
    if any(word in message for word in ['metas', 'goals', 'objetivos', 'establecer metas']):
        return "Establece metas SMART: Específicas, Medibles, Alcanzables, Relevantes, con Tiempo definido."

    # General tips questions
    if any(word in message for word in ['consejos', 'tips', 'advice', 'recomendaciones']):
        return "Consejo general: Vive por debajo de tus posibilidades y construye riqueza gradualmente."

    # Bot identity questions
    if any(word in message for word in ['bot', 'robot', 'ai', 'artificial', 'eres un bot']):
        if plan_data:
            return f"Soy tu asistente financiero personal para '{plan_data['plan'].nombre}'. 🤖💡 ¡Listo para charlar de dinero!"
        return "¡Soy tu compañero financiero! 🤖💰 ¿Qué quieres saber sobre finanzas?"

    # Mood responses
    if any(word in message for word in ['bien', 'good', 'great', 'excelente', 'perfecto']):
        return "¡Genial! 😄 ¿Qué más te preocupa hoy?"

    if any(word in message for word in ['mal', 'bad', 'triste', 'sad', 'horrible']):
        return "Uy, eso no suena bien. ¿Quieres hablar de lo que te preocupa?"

    # Default response
    if plan_data:
        return f"Uy, no entendí eso. 🤔 ¿Quieres que hablemos de tu presupuesto, metas, ahorros o inversiones?"
    return "Hmm, no capté eso. 💭 ¿Quieres charlar de finanzas? Puedo ayudarte con presupuesto, ahorros, inversiones..."

    # Greeting patterns
    if any(word in message for word in ['hola', 'hello', 'hi', 'hey', 'buenos dias', 'buenas tardes']):
        if plan_data:
            return f"¡Hola! 👋 Soy el asistente de '{plan_data['plan'].nombre}'. ¿Qué tal va tu día financiero?"
        return "¡Hola! 👋 Soy tu compañero de finanzas en EcoSmart. ¿Cómo estás?"

    # Goodbye patterns
    if any(word in message for word in ['adios', 'bye', 'chau', 'hasta luego', 'nos vemos']):
        return "¡Chao! 😊 Nos vemos pronto con más consejos financieros."

    # Plan-specific data requests
    if plan_data:
        # Summary/Resumen requests
        if any(word in message for word in ['resumen', 'summary', 'estado', 'status', 'como va', 'how is it going']):
            return get_plan_summary(plan_data)

        # Detailed data analysis
        if any(word in message for word in ['datos', 'data', 'informacion', 'info', 'detalles']):
            return get_detailed_plan_data(plan_data)

        # Budget analysis and advice
        if any(word in message for word in ['presupuesto', 'budget', 'analizar presupuesto', 'budget analysis']):
            return get_budget_analysis(plan_data)

        # Expense breakdown
        if any(word in message for word in ['gastos', 'expenses', 'desglose gastos', 'expense breakdown']):
            return get_expense_breakdown(plan_data)

        # Savings analysis
        if any(word in message for word in ['ahorros', 'savings', 'ahorro', 'analizar ahorros']):
            return get_savings_analysis(plan_data)

        # Goals progress
        if any(word in message for word in ['metas', 'goals', 'objetivos', 'progreso metas']):
            return get_goals_progress(plan_data)

        # Tasks/To-do list
        if any(word in message for word in ['tareas', 'tasks', 'pendientes', 'to do']):
            return get_tasks_summary(plan_data)

        # Investment recommendations based on plan data
        if any(word in message for word in ['invertir', 'invest', 'inversiones', 'investment']):
            return get_investment_recommendations(plan_data)

        # Personalized advice
        if any(word in message for word in ['consejo', 'advice', 'recomendacion', 'sugerencia']):
            return get_personalized_advice(plan_data)

        # Financial education
        if any(word in message for word in ['educacion', 'education', 'aprender', 'learn', 'enseñame']):
            return get_financial_education(plan_data)

        # Market insights
        if any(word in message for word in ['mercado', 'market', 'tendencias', 'trends', 'analisis mercado']):
            return get_market_insights(plan_data)

        # Risk assessment
        if any(word in message for word in ['riesgo', 'risk', 'tolerancia riesgo', 'perfil inversion']):
            return get_risk_assessment(plan_data)

        # Tax optimization
        if any(word in message for word in ['impuestos', 'tax', 'fiscal', 'taxes', 'optimizar impuestos']):
            return get_tax_optimization(plan_data)

        # Estate planning
        if any(word in message for word in ['herencia', 'estate', 'patrimonio', 'sucesion', 'planificacion']):
            return get_estate_planning(plan_data)

    # General economy questions (when no specific plan)
    if any(word in message for word in ['economia', 'economy', 'que es economia', 'what is economy']):
        return "La economía es la ciencia que estudia cómo las personas, empresas y gobiernos utilizan los recursos limitados para satisfacer necesidades ilimitadas. 🤓 ¿Quieres saber sobre algún concepto específico?"

    # General budget questions
    if any(word in message for word in ['presupuesto', 'budget', 'como hacer presupuesto', 'how to budget']):
        return "Para un buen presupuesto: 50% para necesidades, 30% para deseos, 20% para ahorros e inversiones."

    # General savings questions
    if any(word in message for word in ['ahorrar', 'save', 'savings', 'ahorro', 'como ahorrar']):
        return "Recomiendo ahorrar al menos el 20% de tus ingresos. Usa cuentas de ahorro de alto rendimiento."

    # General investment questions
    if any(word in message for word in ['invertir', 'invest', 'inversiones', 'como invertir']):
        return "Diversifica tus inversiones. Considera fondos indexados para principiantes."

    # General expense questions
    if any(word in message for word in ['gastos', 'expenses', 'controlar gastos', 'reducir gastos']):
        return "Analicemos tus gastos. ¿Qué categoría consumes más?"

    # General income questions
    if any(word in message for word in ['ingresos', 'income', 'aumentar ingresos', 'ganar mas']):
        return "Para optimizar ingresos: busca fuentes adicionales, negocia aumentos, invierte en educación."

    # General goal questions
    if any(word in message for word in ['metas', 'goals', 'objetivos', 'establecer metas']):
        return "Establece metas SMART: Específicas, Medibles, Alcanzables, Relevantes, con Tiempo definido."

    # General tips questions
    if any(word in message for word in ['consejos', 'tips', 'advice', 'recomendaciones']):
        return "Consejo general: Vive por debajo de tus posibilidades y construye riqueza gradualmente."

    # Bot identity and knowledge questions
    if any(word in message for word in ['bot', 'robot', 'ai', 'artificial', 'eres un bot', 'conocimientos', 'sabes', 'knowledge', 'que sabes', 'conocimentos']):
        if plan_data:
            return f"Soy EcoSmart AI, tu asistente financiero con conocimientos profundos en economía, inversiones, planificación fiscal y gestión de riesgos. 🤖💡 ¿Qué quieres saber sobre tus finanzas?"
        return "¡Soy EcoSmart AI! Tengo conocimientos avanzados en economía, finanzas personales, inversiones, planificación fiscal y mercados financieros. 🤖💰 ¿Qué tema te interesa?"

    # Mood responses
    if any(word in message for word in ['bien', 'good', 'great', 'excelente', 'perfecto']):
        return "¡Genial! 😄 ¿Qué más te preocupa hoy?"

    if any(word in message for word in ['mal', 'bad', 'triste', 'sad', 'horrible']):
        return "Uy, eso no suena bien. ¿Quieres hablar de lo que te preocupa?"

    # Handle specific economic questions directly
    message_lower = message.lower()

    # Economic concepts dictionary - check for exact phrase matches first
    if 'que es la escasez' in message_lower or message_lower == 'escasez':
        return 'Es la situación en la que los recursos disponibles son insuficientes para cubrir todas las necesidades humanas.'

    if 'que es la economia' in message_lower or 'que es economia' in message_lower or message_lower == 'economia':
        return 'La economía es la ciencia que estudia cómo las personas, empresas y gobiernos utilizan los recursos limitados para satisfacer necesidades ilimitadas.'

    if 'que es el pib' in message_lower or message_lower == 'pib':
        return 'El Producto Interno Bruto mide el valor total de bienes y servicios finales producidos en un país durante un período.'

    if 'que es la inflacion' in message_lower or message_lower == 'inflacion':
        return 'Es el aumento sostenido y generalizado de los precios de bienes y servicios en una economía.'

    if 'que es el desempleo' in message_lower or message_lower == 'desempleo':
        return 'Es la situación en la que personas que buscan trabajo activamente no consiguen empleo.'

    # More economic concepts
    economic_concepts = {
        'bien': 'Los bienes son objetos materiales que satisfacen necesidades (como ropa o comida).',
        'servicio': 'Los servicios son actividades que también satisfacen necesidades (como transporte o educación).',
        'bienes y servicios': 'Los bienes son objetos materiales que satisfacen necesidades (como ropa o comida), y los servicios son actividades que también lo hacen (como transporte o educación).',
        'costo de oportunidad': 'Es el valor de la mejor alternativa que se pierde cuando se elige una opción.',
        'oferta y demanda': 'La oferta representa la cantidad de bienes que los productores están dispuestos a vender, y la demanda, la cantidad que los consumidores desean comprar.',
        'mercado': 'Es el lugar físico o virtual donde se intercambian bienes y servicios entre compradores y vendedores.',
        'microeconomia': 'Analiza el comportamiento individual de consumidores, empresas y mercados específicos.',
        'elasticidad': 'Es la medida de cómo cambia la cantidad demandada de un bien ante un cambio en su precio.',
        'monopolio': 'Es una situación donde una sola empresa domina la oferta de un producto o servicio sin competencia.',
        'competencia perfecta': 'Es un mercado donde hay muchos compradores y vendedores, productos idénticos y libre entrada o salida de empresas.',
        'costos fijos': 'Los costos fijos no cambian con la producción (como el alquiler).',
        'costos variables': 'Los costos variables sí cambian con la producción (como materias primas).',
        'macroeconomia': 'Analiza la economía en su conjunto: crecimiento, inflación, desempleo, política fiscal y monetaria.',
        'deflacion': 'Es la disminución general de los precios en una economía.',
        'politica fiscal': 'Es el uso del gasto público y los impuestos por parte del gobierno para influir en la economía.',
        'politica monetaria': 'Es la regulación de la cantidad de dinero y las tasas de interés, generalmente a cargo del banco central.',
        'presupuesto personal': 'Es una herramienta que permite planificar ingresos y gastos para mantener un equilibrio financiero.',
        'ahorrar': 'Establecé metas claras, registrá tus gastos, eliminá los innecesarios y destiná un porcentaje fijo de tus ingresos al ahorro.',
        'inversion': 'Es el uso de dinero para adquirir activos que puedan generar ganancias futuras.',
        'interes compuesto': 'Es el interés que se calcula sobre el capital inicial más los intereses acumulados anteriormente.',
        'dinero': 'Es un medio de intercambio aceptado para comprar bienes y servicios y pagar deudas.',
        'banco central': 'Es la institución encargada de emitir moneda, controlar la inflación y regular el sistema financiero.',
        'tasa de interes': 'Es el costo del dinero, expresado como porcentaje del monto prestado o invertido.',
        'criptomonedas': 'Son monedas digitales descentralizadas que usan criptografía para asegurar transacciones, como Bitcoin o Ethereum.',
        'comercio internacional': 'Es el intercambio de bienes y servicios entre países.',
        'exportacion': 'Es vender productos al extranjero.',
        'importacion': 'Es comprar productos desde otro país.',
        'aranceles': 'Son impuestos aplicados a productos importados para proteger la producción nacional.',
        'balanza comercial': 'Es la diferencia entre el valor de las exportaciones y las importaciones de un país.',
        'globalizacion': 'Es la creciente interconexión de las economías del mundo mediante el comercio, la inversión y la tecnología.',
        'inflacion argentina': 'Factores como el exceso de emisión monetaria, déficit fiscal, aumento de costos y expectativas inflacionarias.',
        'tipo de cambio': 'Es el valor de una moneda nacional en relación con otra, por ejemplo, cuántos pesos cuesta un dólar.',
        'deficit fiscal': 'Es cuando los gastos del Estado superan sus ingresos.',
        'riesgo pais': 'Es un indicador que mide la probabilidad de que un país no cumpla con sus obligaciones financieras.',
        'economia conductual': 'Es una rama que estudia cómo las emociones y la psicología influyen en las decisiones económicas.',
        'sesgos cognitivos': 'Son errores sistemáticos en la toma de decisiones, como el exceso de confianza o el miedo a perder.',
        'nudge': 'Es una estrategia que modifica el entorno para influir en las decisiones sin imponer reglas.',
        'capitalismo': 'Sistema donde los medios de producción son privados y las decisiones se toman a través del mercado.',
        'socialismo': 'Sistema donde el Estado controla o regula los medios de producción para garantizar igualdad.',
        'economia mixta': 'Es una combinación de mercado libre y control estatal.',
        'impuestos': 'Son aportes obligatorios que los ciudadanos pagan al Estado para financiar servicios públicos.',
        'gasto publico': 'Es el dinero que el Estado usa para proveer servicios como educación, salud y seguridad.',
        'deuda publica': 'Es el dinero que el Estado debe a acreedores nacionales o extranjeros.'
    }

    # Check for partial matches
    for key, response in economic_concepts.items():
        if key in message_lower:
            return response

    # Default response - try Grok AI for unrecognized queries
    try:
        # Quick call to Grok for general questions
        headers = {
            'Authorization': f'Bearer {GROK_API_KEY}',
            'Content-Type': 'application/json'
        }

        quick_prompt = f"""Responde de manera concisa y carismática a esta pregunta económica/financiera: '{message}'
        Mantén la respuesta en 2-3 líneas máximo. Sé amigable y termina con una pregunta si es apropiado."""

        payload = {
            'model': 'grok-beta',
            'messages': [{'role': 'user', 'content': quick_prompt}],
            'max_tokens': 200,
            'temperature': 0.7
        }

        response = requests.post(GROK_API_URL, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            if ai_response and len(ai_response) > 10:  # Valid response
                return ai_response

    except Exception as e:
        pass  # Fall back to default responses

    # Fallback default responses
    if plan_data:
        return f"Uy, no entendí eso. 🤔 ¿Quieres que hablemos de tu presupuesto, metas, ahorros o inversiones?"
    return "Hmm, no capté eso. 💭 ¿Quieres charlar de finanzas? Puedo ayudarte con presupuesto, ahorros, inversiones..."


def get_plan_summary(plan_data):
    """Generate a conversational summary of the plan's financial status"""
    plan = plan_data['plan']
    ingresos = float(plan_data['ingresos'])
    gastos = float(plan_data['gastos'])
    balance = float(plan_data['balance'])
    objetivos = plan_data['objetivos']
    tareas = plan_data['tareas']

    summary = f"¡Hola! Veamos cómo va '{plan.nombre}' 👀\n\n"

    # Financial overview - conversational
    if balance > 0:
        summary += f"💰 Tienes ${balance:,.0f} ahorrados este mes. ¡Bien hecho!\n"
    elif balance == 0:
        summary += f"💰 Estás en cero. Ni gastas más de lo que ganas, ni ahorras. ¿Podemos mejorar eso?\n"
    else:
        summary += f"⚠️ Estás en rojo con ${abs(balance):,.0f}. Necesitamos ajustar el rumbo.\n"

    if ingresos > 0:
        ratio_gastos = (gastos / ingresos) * 100
        if ratio_gastos > 80:
            summary += f"📊 Gastas el {ratio_gastos:.0f}% de tus ingresos. ¿Demasiado?\n"
        elif ratio_gastos < 60:
            summary += f"📊 Solo gastas el {ratio_gastos:.0f}% de tus ingresos. ¡Eres un maestro del ahorro!\n"
        else:
            summary += f"📊 Gastas el {ratio_gastos:.0f}% de tus ingresos. Está en el rango ideal.\n"

    # Goals - engaging
    if objetivos:
        completadas = [obj for obj in objetivos if obj.estado == 'completado']
        pendientes = [obj for obj in objetivos if obj.estado != 'completado']
        if completadas:
            summary += f"🎯 ¡{len(completadas)} metas completadas! Eres una máquina.\n"
        if pendientes:
            obj_cercano = min(pendientes, key=lambda x: (x.monto_actual / x.monto_necesario) if x.monto_necesario > 0 else 0, default=None)
            if obj_cercano:
                progreso = (obj_cercano.monto_actual / obj_cercano.monto_necesario) * 100 if obj_cercano.monto_necesario > 0 else 0
                summary += f"🎯 Tu meta '{obj_cercano.nombre}' está al {progreso:.0f}%. ¡Ya casi!\n"

    # Tasks - brief
    if tareas:
        pendientes = [t for t in tareas if t.estado != 'completada']
        if pendientes:
            summary += f"📝 Tienes {len(pendientes)} tareas pendientes. ¿Empezamos por una?\n"

    # Quick engaging advice
    if balance < 0:
        summary += f"\n💡 ¿Qué tal si reducimos algunos gastos innecesarios?"
    elif balance > ingresos * 0.2:
        summary += f"\n💡 ¡Wow! Superas el 20% de ahorro. ¿Quieres invertir parte?"
    else:
        summary += f"\n💡 ¿Quieres tips para ahorrar más este mes?"

    return summary


def get_detailed_plan_data(plan_data):
    """Provide detailed financial data breakdown"""
    plan = plan_data['plan']
    dinero = plan_data['dinero']

    response = f"📈 **Datos Detallados del Plan '{plan.nombre}'**\n\n"

    # Income breakdown
    ingresos = dinero.ingresos.all()
    if ingresos:
        response += f"💵 **Ingresos por tipo:**\n"
        for ingreso in ingresos:
            response += f"• {ingreso.nombre}: ${ingreso.cantidad:,.0f} ({ingreso.tipo_ingreso})\n"
        response += f"• **Total ingresos:** ${plan_data['ingresos']:,.0f}\n\n"

    # Expense breakdown by category
    gastos = dinero.gastos.all()
    if gastos:
        response += f"💸 **Gastos por categoría:**\n"
        categorias = {}
        for gasto in gastos:
            cat = gasto.tipo_gasto
            if cat not in categorias:
                categorias[cat] = []
            categorias[cat].append(gasto)

        for cat, gastos_cat in categorias.items():
            total_cat = sum(g.cantidad for g in gastos_cat)
            response += f"• **{cat}:** ${total_cat:,.0f}\n"
            for gasto in gastos_cat[:2]:  # Show top 2 expenses per category
                response += f"  - {gasto.nombre}: ${gasto.cantidad:,.0f}\n"

        response += f"\n• **Total gastos:** ${plan_data['gastos']:,.0f}\n"

    # Financial ratios
    if plan_data['ingresos'] > 0:
        response += f"\n📊 **Ratios Financieros:**\n"
        response += f"• Gastos/Ingresos: {(plan_data['gastos']/plan_data['ingresos'])*100:.1f}%\n"
        response += f"• Ahorro/Ingresos: {((plan_data['ingresos']-plan_data['gastos'])/plan_data['ingresos'])*100:.1f}%\n"

    return response


def get_budget_analysis(plan_data):
    """Analyze budget conversationally"""
    ingresos = plan_data['ingresos']
    gastos = plan_data['gastos']
    balance = plan_data['balance']

    if ingresos == 0:
        return "Oye, no veo ingresos registrados. ¿Me cuentas cuánto ganas al mes?"

    ratio_gastos = (gastos / ingresos) * 100

    response = f"Veamos tu presupuesto de '{plan_data['plan'].nombre}' 💸\n\n"

    if ratio_gastos > 80:
        response += f"⚠️ Gastas el {ratio_gastos:.0f}% de tus ingresos. ¡Eso es mucho!\n"
        response += f"💡 ¿Qué tal si cortamos gastos en cafés o delivery?\n"
    elif ratio_gastos > 60:
        response += f"⚡ Gastas el {ratio_gastos:.0f}%. Está alto, pero manejable.\n"
        response += f"💡 ¿Quieres que te ayude a encontrar ahorros?\n"
    else:
        response += f"✅ ¡Excelente! Solo gastas el {ratio_gastos:.0f}%.\n"
        response += f"💡 ¿Quieres tips para invertir ese ahorro extra?\n"

    response += f"\nRecuerda la regla 50/30/20: necesidades, deseos, ahorros."

    return response


def get_expense_breakdown(plan_data):
    """Provide conversational expense analysis"""
    dinero = plan_data['dinero']
    gastos = dinero.gastos.all()

    if not gastos:
        return "No veo gastos registrados. ¿Me cuentas en qué gastas tu dinero?"

    response = f"Veamos tus gastos en '{plan_data['plan'].nombre}' 🔍\n\n"

    # Group expenses by category
    categorias = {}
    for gasto in gastos:
        cat = gasto.tipo_gasto
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(gasto)

    # Sort categories by total amount
    categorias_ordenadas = sorted(categorias.items(),
                                key=lambda x: sum(g.cantidad for g in x[1]),
                                reverse=True)

    total_gastos = plan_data['gastos']

    # Show top 3 categories conversationally
    for i, (cat, gastos_cat) in enumerate(categorias_ordenadas[:3]):
        total_cat = sum(g.cantidad for g in gastos_cat)
        porcentaje = (total_cat / total_gastos) * 100 if total_gastos > 0 else 0

        if i == 0:
            response += f"🥇 Tu mayor gasto es en {cat}: ${total_cat:,.0f} ({porcentaje:.0f}%)\n"
        elif i == 1:
            response += f"🥈 Segundo lugar: {cat} con ${total_cat:,.0f}\n"
        else:
            response += f"🥉 Tercero: {cat} con ${total_cat:,.0f}\n"

    # Quick advice
    if categorias_ordenadas:
        cat_mayor = categorias_ordenadas[0][0]
        response += f"\n💡 ¿Podemos reducir algo en '{cat_mayor}'?"

    return response


def get_savings_analysis(plan_data):
    """Analyze savings conversationally"""
    ingresos = plan_data['ingresos']
    gastos = plan_data['gastos']
    balance = plan_data['balance']

    if ingresos == 0:
        return "Primero necesito saber cuánto ganas. ¿Me lo cuentas?"

    ahorro_mensual = balance
    ratio_ahorro = (ahorro_mensual / ingresos) * 100

    response = f"Hablemos de tus ahorros en '{plan_data['plan'].nombre}' 🏦\n\n"

    if ahorro_mensual > 0:
        response += f"💰 Ahorras ${ahorro_mensual:,.0f} al mes ({ratio_ahorro:.0f}%)\n"
        if ratio_ahorro >= 20:
            response += f"¡Wow! Superas el 20% recomendado. ¡Eres un crack!\n"
        elif ratio_ahorro >= 10:
            response += f"Casi en la meta del 20%. ¡Vas bien!\n"
        else:
            response += f"Estás por debajo del 10%. ¿Aumentamos eso?\n"
    else:
        response += f"⚠️ No estás ahorrando nada este mes.\n"
        response += f"¿Empezamos con el 10% de tus ingresos?\n"

    # Emergency fund - simplified
    if ahorro_mensual > 0 and gastos > 0:
        meses_cobertura = ahorro_mensual / gastos * 12
        if meses_cobertura < 3:
            response += f"🛡️ Tu fondo de emergencia cubre {meses_cobertura:.1f} meses. Apunta a 3-6.\n"

    return response


def get_goals_progress(plan_data):
    """Show engaging goals progress"""
    objetivos = plan_data['objetivos']

    if not objetivos:
        return f"Oye, no tienes metas en '{plan_data['plan'].nombre}'. ¿Creamos una juntos? 🎯"

    response = f"¡Veamos tus metas! 🎯\n\n"

    completadas = [obj for obj in objetivos if obj.estado == 'completado']
    activas = [obj for obj in objetivos if obj.estado == 'pendiente']

    if completadas:
        response += f"✅ ¡{len(completadas)} metas completadas! ¡Bravo!\n"

    if activas:
        # Show the closest to completion first
        obj_cercano = min(activas, key=lambda x: (x.monto_actual / x.monto_necesario) if x.monto_necesario > 0 else 0, default=None)
        if obj_cercano:
            progreso = (obj_cercano.monto_actual / obj_cercano.monto_necesario) * 100 if obj_cercano.monto_necesario > 0 else 0
            restante = obj_cercano.monto_necesario - obj_cercano.monto_actual
            response += f"🔄 '{obj_cercano.nombre}' está al {progreso:.0f}% - te faltan ${restante:,.0f}\n"

        if len(activas) > 1:
            response += f"Tienes {len(activas)} metas activas. ¡Vas por buen camino!\n"

    # Motivational close
    if activas:
        response += f"\n💪 ¿Quieres que te ayude a acelerar alguna meta?"

    return response


def get_financial_education(plan_data):
    """Provide concise financial education"""
    response = f"¡Aprendamos juntos! 📚\n\n"

    # Quick personalized tip based on their situation
    if plan_data['balance'] < 0:
        response += f"💡 **Tip clave:** El interés compuesto es tu mejor amigo. $100 ahorrados hoy valen más mañana.\n\n"
    elif plan_data['balance'] > plan_data['ingresos'] * 0.2:
        response += f"💡 **Tip clave:** Diversifica tus inversiones. No pongas todos los huevos en una canasta.\n\n"
    else:
        response += f"💡 **Tip clave:** La regla 50/30/20: 50% necesidades, 30% deseos, 20% ahorros.\n\n"

    response += f"📖 **Lecturas rápidas:**\n"
    response += f"• 'Padre Rico Padre Pobre' - Robert Kiyosaki\n"
    response += f"• 'El inversor inteligente' - Benjamin Graham\n\n"

    response += f"🎧 **Podcasts:** 'Planet Money' o 'Finanzas para Mortales'\n\n"
    response += f"¿Qué tema te interesa más?"

    return response


def get_market_insights(plan_data):
    """Provide concise market insights"""
    response = f"📊 Mercado actual: acciones suben ~7-10% anual 📈\n\n"

    if plan_data['balance'] < plan_data['ingresos'] * 0.1:
        response += f"Para ti: enfócate en bonos y ahorro seguro primero 🛡️\n"
    elif plan_data['balance'] < plan_data['ingresos'] * 0.3:
        response += f"Para ti: ETFs indexados + algo de bonos ⚖️\n"
    else:
        response += f"Para ti: acciones y bienes raíces 🚀\n"

    response += f"\n💡 Recuerda: invierte regularmente, no intentes timing perfecto."

    return response


def get_risk_assessment(plan_data):
    """Assess risk tolerance concisely"""
    ingresos = float(plan_data['ingresos'])
    balance = float(plan_data['balance'])

    # Simple risk score
    risk_score = 50
    if balance > ingresos * 0.3:
        risk_score += 20
    elif balance < 0:
        risk_score -= 20

    response = f"⚖️ Tu tolerancia al riesgo: {risk_score}/100\n\n"

    if risk_score >= 70:
        response += f"🔥 Agresivo: te van las acciones y cripto 🚀\n"
    elif risk_score >= 50:
        response += f"⚖️ Moderado: ETFs + bonos es tu onda 📈\n"
    else:
        response += f"🛡️ Conservador: ahorro seguro primero 💰\n"

    response += f"\n💡 El riesgo adecuado depende de tu edad y metas."

    return response


def get_tax_optimization(plan_data):
    """Provide concise tax optimization advice"""
    response = f"💼 Impuestos: maximiza deducciones legales 📋\n\n"

    response += f"🏦 **Cuentas inteligentes:**\n"
    response += f"• IRA/Roth IRA: crecen libres de impuestos\n"
    response += f"• 401(k): deducibles de tu sueldo\n\n"

    if plan_data['balance'] > 1000:
        response += f"Para ti: maximiza jubilación antes de invertir.\n"
    elif plan_data['ingresos'] > 50000:
        response += f"Para ti: busca deducciones y créditos fiscales.\n"

    response += f"\n⚠️ Consulta un contador - las leyes cambian."

    return response


def get_estate_planning(plan_data):
    """Provide conversational estate planning advice"""
    response = f"🏛️ Planificación patrimonial: piensa en el futuro de tu familia 👨‍👩‍👧‍👦\n\n"

    response += f"📜 **Lo básico:**\n"
    response += f"• Testamento: di cómo quieres que se distribuyan tus cosas\n"
    response += f"• Beneficiarios: nombra quién recibe qué\n"
    response += f"• Poderes: designa quién decide si no puedes\n\n"

    if plan_data['balance'] > 10000:
        response += f"Para ti: es hora de un testamento y seguros de vida.\n"
    else:
        response += f"Para ti: enfócate en construir patrimonio primero.\n"

    response += f"\n💡 Habla con un abogado especializado."

    return response


def get_tasks_summary(plan_data):
    """Show brief tasks summary"""
    tareas = plan_data['tareas']

    if not tareas:
        return f"Oye, no tienes tareas. ¿Creamos una lista de pendientes? 📝"

    pendientes = [t for t in tareas if t.estado == 'pendiente']
    en_proceso = [t for t in tareas if t.estado == 'en_proceso']
    completadas = [t for t in tareas if t.estado == 'completada']

    response = f"📝 Tus tareas en '{plan_data['plan'].nombre}':\n\n"

    if pendientes:
        response += f"⏳ Pendientes: {len(pendientes)}\n"
        for tarea in pendientes[:3]:
            response += f"• {tarea.nombre}\n"

    if en_proceso:
        response += f"🔄 En proceso: {len(en_proceso)}\n"

    if completadas:
        response += f"✅ Completadas: {len(completadas)}\n"

    response += f"\n💪 ¿Cuál empezamos?"

    return response


def get_investment_recommendations(plan_data):
    """Provide concise investment recommendations"""
    ingresos = plan_data['ingresos']
    balance = plan_data['balance']

    response = f"💰 Inversión para '{plan_data['plan'].nombre}':\n\n"

    if balance < 0:
        response += f"⚠️ Primero arregla tus finanzas básicas.\n"
        response += f"💡 Enfócate en ahorro de emergencia.\n"
    elif balance < ingresos * 0.1:
        response += f"🔰 Principiante: empieza con ahorro de alto rendimiento (4-5%)\n"
        response += f"💡 $100-500 para comenzar.\n"
    elif balance < ingresos * 0.3:
        response += f"📈 Intermedio: ETFs indexados + bonos (60/40)\n"
        response += f"💡 Usa cuentas de jubilación.\n"
    else:
        response += f"🚀 Avanzado: acciones + REITs + algo de crypto\n"
        response += f"💡 Diversifica bien.\n"

    response += f"\n🎯 Regla de oro: invierte lo que puedas perder."

    return response


def get_personalized_advice(plan_data):
    """Generate engaging personalized advice"""
    ingresos = float(plan_data['ingresos'])
    balance = float(plan_data['balance'])
    objetivos = plan_data['objetivos']
    tareas = plan_data['tareas']

    response = f"¡Hola! Vamos a charlar de tus finanzas 💬\n\n"

    if balance < 0:
        response += f"⚠️ Veo que estás en negativo. ¿Qué pasó?\n"
        response += f"💡 Podemos arreglarlo juntos. ¿Quieres empezar por reducir gastos?\n\n"
    elif balance < ingresos * 0.1:
        response += f"📈 Vas por buen camino, pero podemos acelerar.\n"
        response += f"💡 ¿Qué tal si automatizamos el 10% de tus ingresos a ahorros?\n\n"
    else:
        response += f"✅ ¡Impresionante! Estás ahorrando bien.\n"
        response += f"💡 ¿Quieres tips para invertir ese dinero extra?\n\n"

    # Quick goals check
    if objetivos:
        pendientes = [obj for obj in objetivos if obj.estado == 'pendiente']
        if pendientes:
            response += f"🎯 Tienes {len(pendientes)} metas pendientes. ¡Vamos por ellas!\n\n"

    # Tasks motivation
    if tareas:
        pendientes = [t for t in tareas if t.estado != 'completada']
        if pendientes:
            response += f"📝 {len(pendientes)} tareas te esperan. ¿Cuál hacemos primero?\n\n"

    response += f"¿Qué te preocupa más hoy?"

    return response