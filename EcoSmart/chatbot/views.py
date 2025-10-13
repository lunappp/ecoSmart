from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Message
from Planes_app.models import Plan, Suscripcion, Dinero, Ingreso, Gasto, Objetivo, Tarea
import re

# Response database with keywords and responses
RESPONSE_PATTERNS = {
    # Greetings
    'saludos': {
        'keywords': ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'hey', 'hi'],
        'responses': [
            "¡Hola! Soy EcoBot, tu compañero en el mundo de las finanzas. ¿Cómo estás hoy?",
            "¡Hola! ¿Listo para hablar de dinero y metas financieras?",
            "¡Hola! Estoy aquí para ayudarte con tus finanzas. ¿Qué necesitas?"
        ]
    },

    # How are you
    'estado': {
        'keywords': ['cómo estás', 'qué tal', 'cómo te va', 'cómo andas'],
        'responses': [
            "¡Genial! Siempre dispuesto a charlar sobre dinero y metas. ¿Y tú?",
            "¡Excelente! ¿Cómo va tu jornada financiera hoy?",
            "¡Muy bien! ¿En qué puedo ayudarte con tus finanzas?"
        ]
    },

    # Good responses
    'bien': {
        'keywords': ['bien', 'genial', 'excelente', 'muy bien', 'perfecto'],
        'responses': [
            "¡Qué bueno! ¿En qué puedo ayudarte con tus finanzas hoy?",
            "¡Me alegro! ¿Quieres hablar de presupuestos, ahorro o inversiones?",
            "¡Excelente! Estoy aquí para optimizar tus finanzas. ¿Qué tema te interesa?"
        ]
    },

    # Goodbye
    'despedida': {
        'keywords': ['adiós', 'chau', 'hasta luego', 'nos vemos', 'bye'],
        'responses': [
            "¡Hasta luego! Recuerda, el ahorro es el primer paso hacia la libertad financiera.",
            "¡Adiós! No olvides revisar tu presupuesto esta semana.",
            "¡Hasta pronto! Que tengas una excelente semana financiera."
        ]
    },

    # Thanks
    'gracias': {
        'keywords': ['gracias', 'thank you', 'thanks'],
        'responses': [
            "¡De nada! Estoy aquí para hacer que tus finanzas sean más inteligentes.",
            "¡Con gusto! ¿Hay algo más en lo que pueda ayudarte?",
            "¡Para eso estoy! ¿Necesitas más consejos financieros?"
        ]
    },

    # Financial problems
    'problemas_financieros': {
        'keywords': ['problemas con dinero', 'problemas financieros', 'dificultades económicas', 'no me alcanza'],
        'responses': [
            "Entiendo, muchos pasan por eso. ¿Quieres hablar de presupuestos o estrategias de ahorro?",
            "No te preocupes, hay soluciones. ¿Puedes contarme más sobre tu situación?",
            "¡Vamos a solucionarlo! ¿Qué aspecto de tus finanzas te preocupa más?"
        ]
    },

    # Need help
    'ayuda': {
        'keywords': ['necesito ayuda', 'ayuda financiera', 'ayúdame'],
        'responses': [
            "¡Claro! Estoy aquí para eso. ¿Qué aspecto de tus finanzas te preocupa más?",
            "¡Por supuesto! ¿Quieres consejos sobre ahorro, presupuesto o inversiones?",
            "¡Estoy para ayudarte! Cuéntame qué necesitas saber sobre finanzas."
        ]
    },

    # Saving
    'ahorro': {
        'keywords': ['ahorrar', 'ahorro', 'quiero ahorrar', 'cómo ahorrar'],
        'responses': [
            "¡Excelente meta! Empecemos con un presupuesto. ¿Cuánto ganas al mes?",
            "¡Ahorrar es clave! ¿Quieres que te ayude a crear un plan de ahorro personalizado?",
            "¡Genial! El ahorro es la base de la libertad financiera. ¿Qué porcentaje quieres ahorrar?"
        ]
    },

    # Debt
    'deuda': {
        'keywords': ['endeudado', 'deuda', 'debo dinero', 'préstamos'],
        'responses': [
            "No te preocupes, hay formas de salir adelante. Primero, hagamos un plan de pagos.",
            "La deuda es manejable con estrategia. ¿Quieres que te ayude a organizar tus pagos?",
            "¡Vamos a solucionarlo! ¿Cuánto debes y a qué tasa de interés?"
        ]
    },

    # Investments
    'inversiones': {
        'keywords': ['invertir', 'inversión', 'inversiones', 'quiero invertir'],
        'responses': [
            "¡Me encanta! Las inversiones pueden hacer crecer tu dinero. ¿Qué tipo te interesa?",
            "¡Excelente! ¿Prefieres inversiones conservadoras o de mayor riesgo?",
            "¡Vamos a invertir! ¿Tienes experiencia previa o es tu primera vez?"
        ]
    },

    # Budget
    'presupuesto': {
        'keywords': ['presupuesto', 'cómo hacer presupuesto', 'planificar gastos'],
        'responses': [
            "¡El presupuesto es tu mejor aliado! Lista tus ingresos y resta gastos fijos y variables.",
            "¡Perfecto! ¿Quieres que te guíe paso a paso para crear un presupuesto efectivo?",
            "¡Vamos a organizarte! Primero, ¿cuáles son tus ingresos mensuales?"
        ]
    },

    # Spending too much
    'gastos_excesivos': {
        'keywords': ['gasto demasiado', 'gastos excesivos', 'no controlo gastos'],
        'responses': [
            "Todos lo hacemos a veces. Identifiquemos patrones y creemos hábitos de ahorro.",
            "¡No te preocupes! Vamos a analizar tus gastos y encontrar áreas de mejora.",
            "¡Podemos solucionarlo! ¿Quieres que revisemos tus gastos por categorías?"
        ]
    },

    # Advanced Financial Concepts
    'inflacion': {
        'keywords': ['inflación', 'qué es inflación', 'cómo afecta inflación'],
        'responses': [
            "La inflación es el aumento generalizado de precios que reduce el poder adquisitivo. Para protegerte, invierte en activos que superen la inflación como acciones o bienes raíces.",
            "Es cuando el dinero vale menos con el tiempo. Actualmente, la inflación global está alta. ¿Quieres estrategias para proteger tu dinero?",
            "La inflación erosiona el valor de tu dinero. Una regla básica: si la inflación es 3%, necesitas ganar al menos 3% + para mantener tu poder adquisitivo."
        ]
    },

    'interes_compuesto': {
        'keywords': ['interés compuesto', 'qué es interés compuesto', 'cómo funciona interés compuesto'],
        'responses': [
            "¡Es magia financiera! Tus ganancias generan más ganancias. Si inviertes $1000 al 7% anual, en 10 años tendrás $1967. Compuesto es poder.",
            "Es cuando ganas intereses sobre intereses. Albert Einstein lo llamó 'la fuerza más poderosa del universo'. ¿Quieres calcular cuánto crecería tu inversión?",
            "El interés compuesto es tu mejor amigo financiero. Invierte temprano y deja que el tiempo haga el trabajo. ¡Cada año cuenta doble!"
        ]
    },

    # Investment Strategies
    'diversificacion': {
        'keywords': ['diversificación', 'diversificar', 'cómo diversificar', 'riesgo inversión'],
        'responses': [
            "¡La diversificación es clave! No pongas todos los huevos en una canasta. Distribuye entre acciones, bonos, bienes raíces y efectivo.",
            "Diversificar reduce riesgo sin sacrificar retornos. Una cartera típica: 60% acciones, 30% bonos, 10% alternativas. ¿Qué porcentaje tienes en cada uno?",
            "'No diversifiques' dijo alguien que perdió dinero. Diversifica para protegerte de volatilidad en sectores específicos."
        ]
    },

    'fondos_mutuos': {
        'keywords': ['fondos mutuos', 'fondos de inversión', 'etf', 'qué son fondos'],
        'responses': [
            "Los fondos mutuos agrupan dinero de muchos inversionistas para comprar acciones/bonos. Ventajas: diversificación instantánea y gestión profesional.",
            "Son como un carrito de compras financiero: pagas una pequeña tarifa y un experto invierte por ti. Perfectos para principiantes.",
            "ETF y fondos indexados son baratos y siguen el mercado. Warren Buffett recomienda index funds para la mayoría de la gente."
        ]
    },

    'criptomonedas': {
        'keywords': ['bitcoin', 'cripto', 'criptomonedas', 'ethereum', 'blockchain'],
        'responses': [
            "Las cripto son volátiles pero innovadoras. Bitcoin es 'oro digital', Ethereum permite contratos inteligentes. Solo invierte lo que puedas perder.",
            "El blockchain es revolucionario, pero cripto no es para todos. Considera: alta volatilidad, regulación cambiante, pero potencial de crecimiento masivo.",
            "Cripto puede ser parte de tu portafolio (1-5%), pero educa primero. ¿Quieres aprender sobre wallets o exchanges seguros?"
        ]
    },

    'bienes_raices': {
        'keywords': ['bienes raíces', 'propiedades', 'inmuebles', 'realt', 'casas inversión'],
        'responses': [
            "Bienes raíces generan ingresos pasivos y apreciación. Ventajas: apalancamiento, deducciones fiscales, protección contra inflación.",
            "REITs (fondos de inversión inmobiliaria) te permiten invertir en real estate sin comprar propiedades. Dividendos regulares y diversificación.",
            "El real estate es tangible y estable. Pero requiere investigación: ubicación, alquileres, mantenimiento. ¿Interesado en REITs?"
        ]
    },

    # Retirement & Tax Planning
    'jubilacion': {
        'keywords': ['jubilación', 'retiro', 'pensión', 'plan jubilación'],
        'responses': [
            "La jubilación requiere planificación temprana. Regla 4%: retira 4% de tu portafolio anualmente. ¿Cuántos años faltan para tu retiro?",
            "Empieza temprano: el interés compuesto es tu aliado. Calcula necesitar 25x tus gastos anuales para jubilarte cómodamente.",
            "Diversifica: 401k/IRA, bienes raíces, negocios. La jubilación exitosa combina ahorro, inversiones y reducción de gastos."
        ]
    },

    'impuestos': {
        'keywords': ['impuestos', 'tax', 'deducciones', 'ahorro fiscal'],
        'responses': [
            "Los impuestos son inevitables, pero se pueden minimizar. Deducciones, créditos fiscales y cuentas con ventajas tributarias son clave.",
            "Estrategias: maximiza contribuciones a 401k/IRA (pre-tax), usa HSA para gastos médicos, invierte en municipal bonds (libres de impuestos).",
            "Planifica todo el año: harvest de pérdidas fiscales, dona a caridad, considera Roth conversions. Un buen CPA vale oro."
        ]
    },

    # Risk Management
    'riesgo': {
        'keywords': ['riesgo', 'volatilidad', 'proteger inversiones', 'seguro'],
        'responses': [
            "El riesgo es parte de invertir. Diversificación, asset allocation apropiada para tu edad, y mantener emergencias en efectivo son fundamentales.",
            "Regla básica: nunca inviertas dinero que necesites en 5+ años. Usa regla 100-edad para porcentaje en acciones.",
            "Seguros: vida, discapacidad, umbrella. Protegen tu patrimonio. ¿Tienes cobertura adecuada?"
        ]
    },

    # Advanced Topics
    'trading': {
        'keywords': ['trading', 'day trading', 'swing trading', 'opciones'],
        'responses': [
            "Trading requiere educación y disciplina. La mayoría pierde dinero. Enfócate en inversión a largo plazo antes de intentar trading.",
            "Si tradas: usa stop losses, limita posición size (1-2% del portafolio), evita FOMO. La paciencia supera la emoción.",
            "Warren Buffett: 'El mercado es un dispositivo para transferir dinero de impacientes a pacientes'. ¿Tu estilo es trading o inversión?"
        ]
    },

    'emprendimiento': {
        'keywords': ['emprender', 'negocio', 'empresa', 'startup'],
        'responses': [
            "Emprender crea riqueza real. Valida tu idea, crea MVP, busca mentores. El fracaso es parte del aprendizaje.",
            "Finanzas para emprendedores: bootstrapping vs funding, cash flow positivo, métricas clave (CAC, LTV). ¿Qué tipo de negocio?",
            "Riesgo calculado: muchos millonarios crearon empresas. Combina con inversiones tradicionales para diversificación."
        ]
    },

    # Modern Finance
    'fintech': {
        'keywords': ['fintech', 'apps financieras', 'robo advisors', 'banca digital'],
        'responses': [
            "Fintech democratiza las finanzas: Robinhood para trading, Acorns para micro-inversiones, Betterment para robo-advising.",
            "Apps útiles: Mint/Personal Capital para budgeting, Wealthfront/Betterment para inversión automática, Credit Karma para crédito.",
            "La revolución fintech: bajo costo, acceso fácil, pero verifica seguridad y regulación. ¿Qué herramienta financiera buscas?"
        ]
    },

    'sostenibilidad': {
        'keywords': ['sostenible', 'esg', 'inversión social', 'green finance'],
        'responses': [
            "Inversión ESG considera medio ambiente, social y gobernanza. Puedes hacer bien mientras ganas dinero.",
            "Fondos ESG han mostrado retornos competitivos. Invierte en energías renovables, compañías éticas, bonos verdes.",
            "Impacto + retornos: posible. Busca fondos que alinien con tus valores mientras generan alpha."
        ]
    },

    # About me
    'sobre_mi': {
        'keywords': ['quién eres', 'cómo te llamas', 'háblame de ti', 'qué eres'],
        'responses': [
            "Soy EcoBot, tu asistente inteligente para finanzas personales. ¿Y tú?",
            "Soy un chatbot diseñado para ayudarte con consejos de ahorro, presupuestos e inversiones.",
            "¡Hola! Soy EcoBot, aquí para hacer que tu dinero trabaje para ti."
        ]
    },

    # Bored
    'aburrido': {
        'keywords': ['me aburro', 'estoy aburrido', 'aburrido'],
        'responses': [
            "¡No te aburras! Hablemos de inversiones emocionantes o de cómo multiplicar tu dinero.",
            "¡Vamos a divertirnos con finanzas! ¿Quieres saber datos curiosos sobre dinero?",
            "¡Activemos tu lado financiero! ¿Qué tal si hablamos de estrategias millonarias?"
        ]
    },

    # Happy/Sad
    'emociones': {
        'keywords': ['feliz', 'triste', 'contento', 'preocupado'],
        'responses': [
            "¡Me alegro! La felicidad financiera es lo mejor. ¿Qué te hace feliz hoy?",
            "Lo siento. Recuerda, con un buen presupuesto puedes superar obstáculos económicos.",
            "¡Entiendo! Las finanzas afectan nuestro estado de ánimo. ¿Quieres hablar de ello?"
        ]
    },

    # Consejo personalizado
    'consejo': {
        'keywords': ['consejo', 'dame un consejo', 'qué me recomiendas', 'necesito consejo'],
        'responses': [
            "¡Claro! Déjame analizar tu plan y darte un consejo personalizado.",
            "Excelente pregunta. Voy a revisar tu situación financiera y te doy un consejo específico.",
            "¡Perfecto! Analicemos tu plan y te doy recomendaciones personalizadas."
        ]
    }
}

@login_required
def chatbot_view(request, plan_id):
    messages = Message.objects.filter(user=request.user).order_by('timestamp')
    return render(request, 'chatbot/chatbot.html', {
        'messages': messages,
        'plan_id': plan_id
    })

def get_user_plan_data(user):
    """Retrieve comprehensive plan data for the user"""
    try:
        # Get user's active subscriptions
        subscriptions = Suscripcion.objects.filter(usuario=user).select_related('plan')

        if not subscriptions.exists():
            return None

        # For now, get the first plan (could be enhanced to handle multiple plans)
        subscription = subscriptions.first()
        plan = subscription.plan

        # Get financial data
        try:
            dinero = Dinero.objects.get(plan=plan)
            total_money = dinero.total_dinero
            total_expenses = dinero.gasto_total
            total_income = dinero.ingreso_total
        except Dinero.DoesNotExist:
            total_money = 0
            total_expenses = 0
            total_income = 0

        # Get recent transactions (last 30 days)
        from django.utils import timezone
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)

        recent_income = Ingreso.objects.filter(
            dinero__plan=plan,
            fecha_guardado__gte=thirty_days_ago
        ).aggregate(total=models.Sum('cantidad'))['total'] or 0

        recent_expenses = Gasto.objects.filter(
            dinero__plan=plan,
            fecha_guardado__gte=thirty_days_ago
        ).aggregate(total=models.Sum('cantidad'))['total'] or 0

        # Get objectives
        objectives = Objetivo.objects.filter(plan=plan)
        active_objectives = objectives.filter(estado='pendiente')
        completed_objectives = objectives.filter(estado='completado')

        # Get tasks
        tasks = Tarea.objects.filter(plan=plan)
        pending_tasks = tasks.filter(estado='pendiente')
        completed_tasks = tasks.filter(estado='completada')

        return {
            'plan_name': plan.nombre,
            'plan_type': plan.tipo_plan,
            'total_money': float(total_money),
            'total_income': float(total_income),
            'total_expenses': float(total_expenses),
            'recent_income': float(recent_income),
            'recent_expenses': float(recent_expenses),
            'active_objectives_count': active_objectives.count(),
            'completed_objectives_count': completed_objectives.count(),
            'pending_tasks_count': pending_tasks.count(),
            'completed_tasks_count': completed_tasks.count(),
            'objectives': list(active_objectives.values('nombre', 'monto_necesario', 'monto_actual')),
            'pending_tasks': list(pending_tasks.values('nombre', 'tipo_tarea', 'fecha_a_completar')),
        }
    except Exception as e:
        return None

@login_required
def send_message(request, plan_id):
    if request.method == 'POST':
        user_message = request.POST.get('message')
        if user_message:
            # Get user plan data for contextual responses
            plan_data = get_user_plan_data(request.user)

            # Get AI response with plan context
            bot_response = get_ai_response(user_message, plan_data)
            # Save to database
            Message.objects.create(
                user=request.user,
                user_message=user_message,
                bot_response=bot_response
            )
            return JsonResponse({'response': bot_response})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_ai_response(message, plan_data=None):
    try:
        # Convert message to lowercase for better matching
        message_lower = message.lower().strip()

        # Remove punctuation for better keyword matching
        message_clean = re.sub(r'[¿?¡!.,;:]', '', message_lower)

        best_match = None
        best_score = 0

        # Check each pattern for keyword matches
        for category, data in RESPONSE_PATTERNS.items():
            score = 0
            for keyword in data['keywords']:
                # Exact word match gets higher score
                if keyword in message_clean:
                    score += 2
                # Partial match gets lower score
                elif any(keyword_part in message_clean for keyword_part in keyword.split()):
                    score += 1

            # If this category has the highest score so far
            if score > best_score:
                best_score = score
                best_match = category

        # If we found a good match, return a contextual response
        if best_match and best_score > 0:
            import random

            # If user has plan data, provide contextual responses
            if plan_data:
                contextual_response = get_contextual_response(best_match, None, plan_data)
                if contextual_response:
                    return contextual_response

            # Default random response from patterns
            responses = RESPONSE_PATTERNS[best_match]['responses']
            response = random.choice(responses)

            # Add follow-up questions for deeper conversations on complex topics
            follow_ups = {
                'inversiones': [
                    " ¿Te interesan acciones, bonos, fondos mutuos o algo más específico?",
                    " ¿Cuál es tu tolerancia al riesgo: conservador, moderado o agresivo?",
                    " ¿Cuánto tiempo planeas mantener estas inversiones?"
                ],
                'ahorro': [
                    " ¿Cuánto ganas mensualmente? Eso me ayudará a darte metas realistas.",
                    " ¿Qué porcentaje de tus ingresos quieres destinar al ahorro?",
                    " ¿Tienes un fondo de emergencias ya establecido?"
                ],
                'presupuesto': [
                    " ¿Puedes compartir tus ingresos mensuales aproximados?",
                    " ¿Cuáles son tus gastos fijos principales (alquiler, servicios, etc.)?",
                    " ¿En qué categorías sueles gastar más de lo planeado?"
                ],
                'criptomonedas': [
                    " ¿Has invertido en cripto antes o es tu primera vez?",
                    " ¿Qué porcentaje de tu portafolio consideras para cripto?",
                    " ¿Te interesa Bitcoin, Ethereum u otras altcoins?"
                ],
                'jubilacion': [
                    " ¿Cuántos años tienes actualmente?",
                    " ¿Cuántos años faltan para que planees jubilarte?",
                    " ¿Cuánto estimas que necesitas para mantener tu estilo de vida?"
                ],
                'impuestos': [
                    " ¿En qué país resides? Las leyes fiscales varían.",
                    " ¿Eres empleado, freelancer o tienes tu propio negocio?",
                    " ¿Buscas minimizar impuestos o entender deducciones?"
                ]
            }

            # Add follow-up question 30% of the time for eligible topics
            if best_match in follow_ups and random.random() < 0.3:
                response += random.choice(follow_ups[best_match])

            return response

        # Fallback responses for unmatched messages
        fallback_responses = [
            "Hmm, no estoy seguro de entender completamente. ¿Puedes reformular tu pregunta? Estoy aquí para ayudarte con temas financieros.",
            "¡Disculpa! ¿Puedes explicarme mejor qué necesitas? Puedo ayudarte con ahorro, presupuesto, inversiones y más.",
            "No capté del todo tu mensaje. ¿Quieres hablar de algún tema financiero específico?",
            "¡Perdón! ¿Puedes decirlo de otra manera? Quiero asegurarme de darte el mejor consejo financiero."
        ]

        return random.choice(fallback_responses)

    except Exception as e:
        return "Lo siento, tuve un problema procesando tu mensaje. ¿Puedes intentarlo de nuevo? Estoy aquí para ayudarte con tus finanzas."

def get_contextual_response(category, default_responses, plan_data):
    """Generate contextual responses based on user's plan data"""
    try:
        import random

        if category == 'ahorro':
            total_money = plan_data.get('total_money', 0)
            total_income = plan_data.get('total_income', 0)
            total_expenses = plan_data.get('total_expenses', 0)

            if total_money > 0:
                savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0
                if savings_rate > 20:
                    return f"¡Excelente! Veo que en tu plan '{plan_data['plan_name']}' tienes una tasa de ahorro del {savings_rate:.1f}%. ¡Sigue así!"
                elif savings_rate > 10:
                    return f"Bien hecho con tu plan '{plan_data['plan_name']}'. Tu tasa de ahorro es del {savings_rate:.1f}%. ¿Quieres estrategias para aumentarla?"
                else:
                    return f"En tu plan '{plan_data['plan_name']}' veo oportunidades para mejorar el ahorro. Actualmente tienes ${total_money:.2f} disponibles. ¿Quieres crear un plan de ahorro personalizado?"
            else:
                return f"Veo que tu plan '{plan_data['plan_name']}' está empezando. ¡El ahorro temprano es clave! ¿Quieres que te ayude a establecer metas realistas?"

        elif category == 'presupuesto':
            total_expenses = plan_data.get('total_expenses', 0)
            recent_expenses = plan_data.get('recent_expenses', 0)

            if total_expenses > 0:
                return f"Analizando tu plan '{plan_data['plan_name']}', has gastado ${total_expenses:.2f} en total. En los últimos 30 días: ${recent_expenses:.2f}. ¿Quieres que revisemos tus categorías de gastos?"
            else:
                return f"Tu plan '{plan_data['plan_name']}' parece estar bien organizado. ¿Quieres que te ayude a crear un presupuesto detallado?"

        elif category == 'inversiones':
            total_money = plan_data.get('total_money', 0)

            if total_money > 10000:
                return f"¡Impresionante! Tu plan '{plan_data['plan_name']}' tiene ${total_money:.2f} disponibles. Con ese capital, podrías considerar diversificar en acciones, bonos y fondos indexados. ¿Qué tipo de inversión te interesa?"
            elif total_money > 1000:
                return f"Tu plan '{plan_data['plan_name']}' tiene un buen inicio con ${total_money:.2f}. Podrías empezar con fondos indexados de bajo costo. ¿Quieres aprender sobre opciones de inversión seguras?"
            else:
                return f"Para tu plan '{plan_data['plan_name']}', recomiendo primero construir un fondo de emergencias antes de invertir. ¿Quieres estrategias para aumentar tus ahorros?"

        elif category == 'problemas_financieros':
            total_money = plan_data.get('total_money', 0)
            pending_tasks = plan_data.get('pending_tasks_count', 0)
            active_objectives = plan_data.get('active_objectives_count', 0)

            response = f"Entiendo que necesitas ayuda financiera con tu plan '{plan_data['plan_name']}'. "
            if total_money < 0:
                response += "Veo que tienes saldo negativo. Prioricemos reducir gastos y aumentar ingresos. "
            if pending_tasks > 0:
                response += f"Tienes {pending_tasks} tareas pendientes que podrían ayudar. "
            if active_objectives > 0:
                response += f"Y {active_objectives} objetivos activos. ¿Por dónde quieres empezar?"
            return response

        elif category == 'gastos_excesivos':
            recent_expenses = plan_data.get('recent_expenses', 0)
            total_expenses = plan_data.get('total_expenses', 0)

            if recent_expenses > 0:
                return f"En tu plan '{plan_data['plan_name']}', has gastado ${recent_expenses:.2f} en los últimos 30 días. ¿Quieres que analicemos juntos dónde se están yendo tus gastos?"
            else:
                return f"Para tu plan '{plan_data['plan_name']}', podemos identificar patrones de gastos. ¿En qué categorías sueles gastar más?"

        elif category == 'consejo':
            # Comprehensive plan analysis for personalized advice
            total_money = plan_data.get('total_money', 0)
            total_income = plan_data.get('total_income', 0)
            total_expenses = plan_data.get('total_expenses', 0)
            recent_income = plan_data.get('recent_income', 0)
            recent_expenses = plan_data.get('recent_expenses', 0)
            active_objectives = plan_data.get('active_objectives_count', 0)
            pending_tasks = plan_data.get('pending_tasks_count', 0)
            plan_name = plan_data.get('plan_name', 'tu plan')

            # Analyze financial health
            if total_money < 0:
                return f"💰 **Análisis de tu plan '{plan_name}':** Veo que tienes saldo negativo (${total_money:.2f}). **Mi consejo prioritario:** Reduce gastos innecesarios inmediatamente y crea un presupuesto de emergencia. Considera ingresos adicionales temporales mientras estabilizas tus finanzas."

            # Calculate savings rate
            savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0

            if savings_rate < 10 and total_income > 0:
                return f"📊 **Análisis de tu plan '{plan_name}':** Tu tasa de ahorro es del {savings_rate:.1f}%, lo que está por debajo del recomendado (20%). **Mi consejo:** Identifica gastos hormiga y automatiza transferencias de ahorro. Comienza con el 15% de tus ingresos."

            if active_objectives == 0 and total_money > 1000:
                return f"🎯 **Análisis de tu plan '{plan_name}':** Tienes buen capital disponible (${total_money:.2f}) pero ningún objetivo activo. **Mi consejo:** Establece metas SMART (Específicas, Medibles, Alcanzables, Relevantes, Temporales). ¿Quieres que te ayude a crear tu primer objetivo?"

            if pending_tasks > 5:
                return f"📝 **Análisis de tu plan '{plan_name}':** Tienes {pending_tasks} tareas pendientes. **Mi consejo:** Prioriza las 3 más importantes esta semana. El progreso constante es mejor que la perfección."

            if total_money > 10000 and savings_rate > 20:
                return f"🚀 **Análisis de tu plan '{plan_name}':** ¡Excelente situación financiera! Con ${total_money:.2f} y {savings_rate:.1f}% de ahorro, estás en gran forma. **Mi consejo:** Considera diversificar inversiones o aumentar tus objetivos de ahorro."

            if recent_expenses > recent_income:
                return f"⚠️ **Análisis de tu plan '{plan_name}':** Tus gastos recientes (${recent_expenses:.2f}) superan tus ingresos (${recent_income:.2f}). **Mi consejo:** Revisa tu presupuesto semanalmente y establece límites de gasto por categoría."

            # Default positive advice
            return f"💡 **Análisis de tu plan '{plan_name}':** Tu situación financiera se ve sólida. **Mi consejo general:** Mantén el hábito de revisar tus finanzas semanalmente, continúa ahorrando consistentemente y establece nuevos objetivos desafiantes."

        # For other categories, return None to use default responses
        return None

    except Exception as e:
        return None