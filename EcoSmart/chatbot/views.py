from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Message
from Planes_app.models import Plan, Suscripcion
import openai
import os
import random

@login_required
def chatbot_view(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    # Verificar que el usuario esté suscrito al plan
    suscripcion = get_object_or_404(Suscripcion, usuario=request.user, plan=plan)
    messages = Message.objects.filter(user=request.user, plan=plan).order_by('timestamp')
    return render(request, 'chatbot/chatbot.html', {'messages': messages, 'plan': plan})

@login_required
def send_message(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    # Verificar que el usuario esté suscrito al plan
    suscripcion = get_object_or_404(Suscripcion, usuario=request.user, plan=plan)

    if request.method == 'POST':
        user_message = request.POST.get('message')
        if user_message:
            # Get AI response with plan context
            bot_response = get_ai_response(user_message, plan)
            # Save to database
            Message.objects.create(
                user=request.user,
                plan=plan,
                user_message=user_message,
                bot_response=bot_response
            )
            return JsonResponse({'response': bot_response})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_ai_response(message, plan):
    # Obtener datos financieros del plan
    try:
        dinero = plan.dinero
        ingresos = dinero.ingresos.all()
        gastos = dinero.gastos.all()
        objetivos = plan.objetivos.all()
        tareas = plan.tareas.all()
        
        # Conteo para respuestas proactivas
        tareas_pendientes_count = tareas.filter(estado__in=['pendiente', 'en_proceso']).count()
        objetivos_activos_count = objetivos.filter(estado='activo').count()

        # Construir contexto financiero
        contexto = f"""
        Información financiera del plan "{plan.nombre}":

        Dinero total: ${float(dinero.total_dinero):.2f}
        Gasto total: ${float(dinero.gasto_total):.2f}
        Ingreso total: ${float(dinero.ingreso_total):.2f}

        Ingresos recientes:
        """
        for ingreso in ingresos.order_by('-fecha_guardado')[:5]:
            contexto += f"- {ingreso.nombre}: ${float(ingreso.cantidad):.2f} ({ingreso.tipo_ingreso})\n"

        contexto += "\nGastos recientes:\n"
        for gasto in gastos.order_by('-fecha_guardado')[:5]:
            contexto += f"- {gasto.nombre}: ${float(gasto.cantidad):.2f} ({gasto.tipo_gasto})\n"

        contexto += "\nObjetivos:\n"
        for objetivo in objetivos:
            contexto += f"- {objetivo.nombre}: ${float(objetivo.monto_actual):.2f}/${float(objetivo.monto_necesario):.2f} ({objetivo.estado})\n"

        contexto += "\nTareas pendientes:\n"
        for tarea in tareas.filter(estado__in=['pendiente', 'en_proceso']):
            contexto += f"- {tarea.nombre}: {tarea.estado}\n"

        # Sistema avanzado de conversación inteligente - Aprendiendo de Grok
        message_lower = message.lower()

        # --- A. Interacciones Simples Mejoradas (Finanzas Conductuales) ---
        
        # Meta-conversación: El chatbot reconoce que es una IA avanzada
        if any(word in message_lower for word in ['grok', 'xai', 'ia', 'inteligencia', 'artificial', 'aprendiendo', 'enseñar']):
            meta_responses = [
                "¡Interesante! 🤖 Como IA financiera avanzada, tengo conocimientos profundos sobre macroeconomía, microeconomía, teoría de portafolios, econometría y mercados financieros globales. ¿En qué aspecto de tus finanzas puedo ayudarte?",
                "¡Tienes razón! 💡 Estoy equipado con algoritmos avanzados de machine learning para análisis financiero, modelos econométricos predictivos y algoritmos de optimización de portafolios. Puedo ayudarte con presupuestos, inversiones, ahorro y planificación estratégica. ¿Qué te gustaría explorar?",
                "¡Exacto! 🎯 Mi sistema de IA está diseñado para entender patrones financieros complejos, analizar riesgos de inversión usando Value at Risk (VaR), y ofrecer consejos basados en teoría financiera moderna. ¿Quieres que analicemos tu situación financiera?",
                "¡Qué perceptivo! 🧠 Como IA especializada en finanzas, domino macroeconomía keynesiana y monetarista, teoría del portafolio moderno de Markowitz, y análisis técnico avanzado. ¿Cómo puedo ayudarte a optimizar tus finanzas?"
            ]
            return random.choice(meta_responses)

        # Saludos con personalidad y conocimientos financieros
        if any(word in message_lower for word in ['hola', 'buenas', 'saludos', 'hey', 'hi', 'qué tal', 'como estas']):
            saludos = [
                f"¡Hola! 👋 Soy Eco, tu asesor financiero personal de EcoSmart. Un **secreto de las finanzas conductuales** es pagar tus deudas pequeñas primero para generar un 'momentum de victoria'. ¿Cómo va tu plan '{plan.nombre}' hoy?",
                f"¡Buen día! 🌞 Soy Eco, tu compañero financiero. Recuerda el **efecto ancla**: si estableces una meta de ahorro ambiciosa, es más probable que ahorres más. ¿Listo para optimizar tus finanzas?",
                f"¡Hola, hola! 😊 Soy Eco. Mi conocimiento en mercados financieros me dice que la **consistencia** es más importante que la cantidad al empezar a ahorrar. ¿Qué tal va tu jornada financiera?",
                f"¡Saludos! 🙌 Soy Eco, tu asesor de confianza. Un gran error es la **contabilidad mental** incorrecta; ¡trata todo tu dinero como una sola unidad! ¿Qué te trae por aquí?"
            ]
            return random.choice(saludos)

        # Agradecimientos con conocimientos financieros y proactividad
        elif any(word in message_lower for word in ['gracias', 'thank', 'agradezco', 'thanks', 'genial']):
            if tareas_pendientes_count > 0:
                agradecimientos = [
                    f"¡De nada! 😊 Estoy aquí para ayudarte. Por cierto, noté que tienes **{tareas_pendientes_count} tareas** pendientes. ¿Quieres que te ayude a priorizarlas y generar un **'quick win'**?",
                    f"¡Con gusto! 🙏 Un buen inversor siempre busca la siguiente oportunidad. ¿Quieres que analicemos si tu **fondo de emergencia** (3-6 meses de gastos) está completo?",
                    f"¡Es un placer ayudarte! 💪 ¿Qué más te gustaría saber sobre tus finanzas? Podríamos revisar si tienes alguna **deuda de alto interés** pendiente.",
                ]
            else:
                 agradecimientos = [
                    "¡De nada! 😊 Estoy aquí para ayudarte con tus finanzas. Mi conocimiento en economía conductual me permite darte consejos realmente efectivos. ¿Hay algo más en lo que pueda asistirte?",
                    "¡Con gusto! 🙏 Tengo expertise en planificación financiera, inversiones y análisis de riesgos. ¿Qué más te gustaría saber sobre tus finanzas?",
                    "¡Es un placer ayudarte! 💪 Mi algoritmo analiza patrones financieros complejos para darte recomendaciones personalizadas. ¿Necesitas más consejos o tienes otras preguntas?",
                    "¡No hay de qué! 🌟 Estoy equipado con conocimientos avanzados en mercados financieros y estrategias de ahorro. ¿Hay algún otro aspecto que quieras explorar?"
                 ]
            return random.choice(agradecimientos)

        # --- B. Bloques de Conocimiento Expandido ---

        # Nuevo: Análisis de Deudas y Crédito
        elif any(word in message_lower for word in ['deuda', 'deudas', 'credito', 'intereses', 'hipoteca', 'prestamo', 'tarjeta', 'pago']):
            deudas_responses = [
                "📋 Deudas e Intereses: La clave es priorizar por **tasa de interés**. Recomiendo el método **Avalancha** (pagar la deuda con el interés más alto) para maximizar el ahorro. ¿Quieres que revisemos tus deudas para encontrar la de mayor impacto?",
                "💳 Salud Crediticia: Un pilar financiero es tu score crediticio. Para mejorarlo, mantén la utilización de tus tarjetas **por debajo del 30% del límite total**. ¿Conoces tu **Ratio de Servicio de Deuda**?",
                "📉 Estrategia de Deuda: Considera si tienes deudas **'buenas'** (ej. hipoteca, inversión) y **'malas'** (ej. tarjetas de crédito). Concéntrate en eliminar las 'malas'. ¿Tienes alguna deuda que te quite el sueño?",
                "💰 Tasa de Interés: El costo de oportunidad de tu dinero. Cada dólar que pagas en intereses es un dólar que no trabaja para ti. ¿Quieres que calculemos cuánto te costará tu deuda actual a largo plazo?",
            ]
            return random.choice(deudas_responses)

        # Nuevo: Inversión, Riesgo y Portafolio
        elif any(word in message_lower for word in ['invertir', 'inversion', 'portafolio', 'diversificar', 'riesgo', 'rentabilidad', 'markowitz', 'beta', 'alfa']):
            inversion_responses = [
                "📈 Inversión y Rentabilidad: El motor de la riqueza es el **Interés Compuesto** a largo plazo. La mejor estrategia es la diversificación pasiva con ETFs de bajo costo. ¿Conocemos tu **tolerancia al riesgo** actual?",
                "🎯 Gestión de Riesgo: En finanzas, riesgo significa volatilidad. La **Teoría Moderna del Portafolio de Markowitz** busca maximizar la rentabilidad para un nivel de riesgo dado. ¿Quieres que comparemos tu perfil de riesgo con tu edad y objetivos?",
                "⚖️ Diversificación: La clave es la baja correlación entre activos. ¿Tu portafolio incluye activos de renta fija, renta variable, y quizás una pequeña asignación a bienes raíces o commodities? El exceso de concentración es el mayor riesgo.",
                "📊 Indicadores Clave: Para evaluar una inversión, mira la **relación Beta** (volatilidad vs. el mercado) y el **Ratio de Sharpe** (rentabilidad ajustada por riesgo). ¿Qué activo en tu portafolio te genera más dudas?"
            ]
            return random.choice(inversion_responses)
        
        # --- C. Bloques Originales (Optimizados y Manteniendo la Heurística) ---
        
        # Resumen financiero
        elif any(word in message_lower for word in ['resumen', 'estado', 'situacion', 'como van', 'como estoy']):
            resumenes = [
                f"¡Claro! Déjame mostrarte cómo van tus finanzas en '{plan.nombre}':\n\n{contexto.strip()}\n\n¿Te parece bien la situación o quieres que profundice en algún aspecto específico? 🤔",
                f"¡Perfecto! Aquí tienes un panorama completo de tu situación financiera:\n\n{contexto.strip()}\n\n¿Hay algo que te llame la atención o quieres que te dé consejos sobre algún punto? 📊",
                f"¡Excelente pregunta! Tu resumen financiero actual es:\n\n{contexto.strip()}\n\n¿Te gustaría que te ayude a mejorar algún aspecto de estos números? 💡"
            ]
            return random.choice(resumenes)

        # Análisis de gastos
        elif any(word in message_lower for word in ['gasto', 'gastos', 'gaste', 'compras']):
            total_gastos = sum(float(gasto.cantidad) for gasto in gastos)
            ingreso_total = float(dinero.ingreso_total)
            # Regla del 70% de ingresos vs. Gastos
            if ingreso_total > 0 and total_gastos > ingreso_total * 0.7:
                consejos_gastos_altos = [
                    f"🤔 Hmm, veo que tus gastos están en ${total_gastos:.2f}, que es más del 70% de tus ingresos. ¡No te preocupes! Te recomiendo identificar 2-3 gastos que puedas reducir esta semana. ¿Quieres que te ayude a categorizar tus gastos para encontrar oportunidades de ahorro?",
                    f"📈 Tus gastos están un poco altos (${total_gastos:.2f}). ¡Pero hey, eso es normal a veces! La clave es la consistencia. ¿Qué tal si aplicamos el **método del presupuesto base cero** (Zero-Based Budgeting)? ¿Te ayudo con eso?",
                    f"💭 Analizando tus gastos... Están en ${total_gastos:.2f}, lo que podría comprometer tu 20% de ahorro. ¿Quieres que revisemos tus últimos 5 gastos para ver dónde podemos aplicar el **principio de Pareto (80/20)** a tu presupuesto?"
                ]
                return random.choice(consejos_gastos_altos)
            else:
                elogios_gastos = [
                    f"¡Excelente! 🎉 Tus gastos están muy bien controlados (${total_gastos:.2f}). ¡Sigue así! ¿Quieres que te ayude a optimizar aún más o prefieres hablar de otro aspecto?",
                    f"¡Bravo! 👏 Tus gastos están en un nivel perfecto (${total_gastos:.2f}). Estás manejando muy bien tu dinero. ¿Te gustaría consejos para invertir esa diferencia o mantener este buen ritmo?",
                    f"¡Impresionante! 🌟 Tus gastos están bajo control (${total_gastos:.2f}). ¡Eso es ser un maestro financiero! ¿Quieres que analicemos cómo potenciar tus ahorros?"
                ]
                return random.choice(elogios_gastos)

        # Consejos sobre ahorro
        elif any(word in message_lower for word in ['ahorro', 'ahorrar', 'guardar', 'saving']):
            total_dinero = float(dinero.total_dinero)
            if total_dinero > 0:
                consejos_ahorro_positivo = [
                    f"¡Genial! 💰 Tienes ${total_dinero:.2f} disponibles. Una regla de oro es ahorrar el 20% de tus ingresos. ¿Quieres que te ayude a crear un objetivo de ahorro específico y motivador?",
                    f"¡Excelente base! 🎯 Con ${total_dinero:.2f} en tu bolsillo, tienes un gran punto de partida. ¿Qué tal si pensamos en invertir parte de ese dinero? ¿Te intereso algún tipo de inversión?",
                    f"¡Muy bien! 🚀 Tienes ${total_dinero:.2f} listos para trabajar. ¿Quieres que te dé estrategias específicas para hacer crecer ese dinero?"
                ]
                return random.choice(consejos_ahorro_positivo)
            else:
                consejos_ahorro_negativo = [
                    "🤝 No te preocupes, ¡todos hemos pasado por eso! Lo importante es actuar ahora. ¿Quieres que te ayude a crear un plan de recuperación financiera paso a paso?",
                    "¡Hey, tranquilo! 💪 Las finanzas son un maratón, no un sprint. Vamos a analizar juntos qué podemos hacer para volver a números positivos. ¿Empezamos?",
                    "¡No hay problema! 😊 Lo bueno es que estás aquí buscando mejorar. ¿Quieres que revisemos juntos tus ingresos y gastos para encontrar oportunidades de mejora?"
                ]
                return random.choice(consejos_ahorro_negativo)

        # Objetivos
        elif any(word in message_lower for word in ['objetivo', 'meta', 'goal', 'planes']):
            if objetivos.exists():
                if objetivos_activos_count > 0:
                    motivaciones = [
                        f"¡Fantástico! 🎯 Tienes {objetivos_activos_count} objetivos activos. ¡Eso demuestra compromiso! Recuerda: el ahorro constante es tu mejor aliado. ¿Quieres que te ayude a acelerar el progreso de alguno?",
                        f"¡Me encanta! 🌟 Tus {objetivos_activos_count} objetivos activos muestran que vas en serio. ¿Quieres que te dé tips para mantener la motivación y alcanzarlos más rápido?",
                        f"¡Impresionante! 💪 {objetivos_activos_count} objetivos activos es señal de que eres proactivo. ¿Te gustaría que analizáramos el progreso de cada uno y ajustáramos la estrategia?"
                    ]
                    return random.choice(motivaciones)
                else:
                    motivaciones_sin_activos = [
                        "¡No hay objetivos activos ahora, pero eso es una oportunidad! 🎯 ¿Quieres que te ayude a crear objetivos nuevos y emocionantes? Podemos empezar con algo pequeño pero significativo.",
                        "¡Perfecto momento para nuevos comienzos! 🌱 ¿Qué tal si creamos juntos algunos objetivos financieros motivadores? ¿Tienes alguna meta específica en mente?",
                        "¡Genial! 📝 Vamos a llenar ese espacio con objetivos increíbles. ¿Qué te gustaría lograr? ¿Un viaje, una casa, o simplemente más tranquilidad financiera?"
                    ]
                    return random.choice(motivaciones_sin_activos)
            else:
                invitaciones_objetivos = [
                    "¡Empecemos entonces! 🎯 Los objetivos son como GPS financiero. ¿Qué te gustaría lograr? ¿Ahorrar para unas vacaciones, crear un fondo de emergencias, o invertir en tu futuro?",
                    "¡Me encanta la idea! 🚀 Vamos a crear objetivos que te motiven. ¿Prefieres metas a corto plazo (3-6 meses) o a largo plazo (1-2 años)?",
                    "¡Excelente actitud! 💡 Los objetivos dan propósito a tus finanzas. ¿Quieres que te ayude a definir uno específico y realista para empezar?"
                ]
                return random.choice(invitaciones_objetivos)

        # Preguntas sobre economía global y mercados
        elif any(word in message_lower for word in ['economia', 'mercado', 'inflacion', 'recesion', 'crisis', 'dolar', 'euro', 'bitcoin', 'cripto', 'bolsa', 'acciones', 'bonos', 'commodities']):
            economia_responses = [
                "📊 Sobre economía global: Actualmente estamos en un entorno de 'inflación moderada' post-pandemia. Los bancos centrales mantienen políticas monetarias restrictivas, pero los mercados laborales siguen fuertes. ¿Quieres que analicemos cómo esto afecta tus inversiones personales?",
                "💹 Mercados financieros: El S&P 500 ha mostrado resiliencia gracias a las ganancias corporativas sólidas, pero la volatilidad del sector tecnológico continúa. Los bonos del tesoro ofrecen rendimientos atractivos comparados con años anteriores. ¿Te interesa alguna estrategia específica?",
                "💰 Inflación y poder adquisitivo: La inflación global ronda el 2-3% en economías desarrolladas, pero alcanza niveles más altos en mercados emergentes. Esto erosiona el valor del dinero en efectivo. ¿Quieres consejos sobre cómo protegerte contra la inflación?",
                "🌍 Economía internacional: China representa el 18% del PIB global, mientras que EE.UU. mantiene su liderazgo en innovación tecnológica. Las tensiones comerciales y geopolíticas añaden volatilidad. ¿Cómo impacta esto en tu planificación financiera?",
                "📈 Ciclos económicos: Estamos en la fase tardía de expansión del ciclo económico. Los indicadores adelantados sugieren cautela, pero no recesión inmediata. Es buen momento para rebalancear portafolios. ¿Quieres que revisemos tu asignación de activos?",
                "₿ Criptomonedas: Bitcoin ha evolucionado de activo especulativo a reserva de valor digital, con una capitalización de mercado de ~$1.2T. Ethereum domina el sector DeFi. ¿Te interesa el análisis técnico o fundamental de alguna cripto?",
                "🏛️ Política monetaria: La FED mantiene tasas en 5.25-5.50%, mientras el BCE lucha con fragmentación en la eurozona. Los bancos centrales emergentes siguen políticas más acomodaticias. ¿Cómo afectan estas decisiones tus finanzas?"
            ]
            return random.choice(economia_responses)

        # Consejos generales con conocimientos avanzados
        elif any(word in message_lower for word in ['consejo', 'recomendacion', 'tip', 'idea']):
            consejos_generales = [
                "💡 Estrategia avanzada: Implementa la regla 50/30/20 (50% necesidades, 30% deseos, 20% ahorro/inversión). Es un marco probado por economistas conductuales.",
                "🎯 Consejo de inversión: Diversifica tu portafolio usando el principio moderno de Markowitz. No pongas todos tus huevos en una canasta.",
                "📊 Análisis técnico: Monitorea tu ratio deuda/ingreso. Debe mantenerse por debajo del 36% para estabilidad financiera óptima.",
                "🚀 Estrategia de crecimiento: Combina el ahorro automático con inversiones indexadas de bajo costo. Es la fórmula que han usado los millonarios.",
                "💪 Economía conductual: Usa el 'efecto ancla' a tu favor. Establece metas de ahorro ambiciosas pero realistas para motivarte.",
                "🎪 Finanzas cuantitativas: Calcula tu retorno sobre inversión (ROI) en todas tus decisiones financieras, desde compras hasta inversiones.",
                "🌟 Teoría financiera: Aprovecha el interés compuesto. Einstein lo llamaba 'la octava maravilla del mundo' por su poder exponencial.",
                "🎨 Psicología financiera: Crea 'cuentas mentales' para diferentes objetivos. Tu cerebro procesa mejor el dinero cuando está categorizado.",
                "📈 Análisis fundamental: Antes de invertir, estudia el modelo de negocio, ventajas competitivas y gestión de la empresa.",
                "🔄 Flujo de caja: Mantén siempre 3-6 meses de gastos en liquidez. Es tu seguro contra volatilidad económica.",
                "📊 Presupuesto cero: Asigna el 100% de tus ingresos a gastos, ahorro e inversión. Nada debe quedar sin asignar.",
                "🎯 Meta SMART: Establece objetivos financieros Específicos, Medibles, Alcanzables, Relevantes y con Tiempo definido."
            ]
            return random.choice(consejos_generales)

        # Preguntas sobre tendencias económicas actuales
        elif any(word in message_lower for word in ['tendencia', 'futuro', 'pronostico', 'prediccion', '2025', '2026', 'proximo', 'siguiente']):
            tendencias_responses = [
                "🔮 Tendencias económicas 2025: La IA y automatización transformarán el mercado laboral. Se espera crecimiento del 2.5-3% global, con foco en energías renovables y semiconductores. ¿Quieres que analicemos cómo adaptar tu portafolio a estas tendencias?",
                "📊 Predicciones macro: Los mercados emergentes (Brasil, India, México) superarán el crecimiento de economías desarrolladas. La digitalización acelerará con 5G y edge computing. ¿Te interesa cómo invertir en estas tendencias?",
                "🌍 Economía sostenible: Las inversiones ESG (Ambiental, Social, Gobernanza) representarán el 50% de activos para 2025. Las empresas con bajas emisiones de carbono tendrán prima. ¿Quieres estrategias de inversión sostenible?",
                "💹 Tecnología financiera: Las fintech revolucionarán los pagos y créditos. Blockchain y DeFi democratizarán las finanzas. ¿Te gustaría explorar oportunidades en este sector emergente?",
                "🏛️ Política económica: Los bancos centrales adoptarán marcos de 'inflación flexible'. Las monedas digitales de bancos centrales (CBDC) podrían reemplazar efectivo. ¿Cómo prepararte para estos cambios?",
                "📈 Demografía económica: El envejecimiento poblacional en occidente contrastará con crecimiento demográfico en África y Asia. Esto creará oportunidades en healthcare y educación. ¿Interesado en estos sectores?"
            ]
            return random.choice(tendencias_responses)

        # Preguntas específicas sobre conceptos económicos
        elif any(word in message_lower for word in ['que es', 'definicion', 'explica', 'concepto']):
            if 'inflacion' in message_lower:
                return "💹 La inflación es el aumento generalizado y sostenido de los precios de bienes y servicios en una economía durante un período de tiempo. Esto provoca una disminución del poder adquisitivo de la moneda, es decir, que con la misma cantidad de dinero se pueden comprar menos cosas. La inflación se mide comúnmente a través del IPC (Índice de Precios al Consumidor)."
            elif 'deflacion' in message_lower:
                return "📉 La deflación es lo contrario de la inflación: es la disminución generalizada y sostenida de los precios de bienes y servicios. Aunque puede parecer positiva inicialmente, la deflación prolongada puede ser perjudicial porque desalienta el consumo y el gasto, lo que puede llevar a recesiones económicas."
            elif 'pib' in message_lower or 'producto interno bruto' in message_lower:
                return "📊 El PIB (Producto Interno Bruto) es el valor total de todos los bienes y servicios finales producidos dentro de las fronteras de un país durante un período específico, generalmente un año. Es la medida más utilizada del tamaño y el crecimiento de una economía."
            elif 'recesion' in message_lower:
                return "📈 Una recesión es un período de contracción económica generalizada caracterizado por una disminución significativa de la actividad económica, que dura al menos dos trimestres consecutivos. Se mide por caídas en el PIB, el empleo, la manufactura y el comercio minorista."
            elif 'interes compuesto' in message_lower:
                return "🚀 El interés compuesto es el interés que se calcula sobre el capital inicial más el interés acumulado de períodos anteriores. Es como 'ganar intereses sobre intereses'. Albert Einstein lo llamó 'la octava maravilla del mundo' por su poder exponencial en el crecimiento de inversiones."
            elif 'diversificacion' in message_lower:
                return "🎯 La diversificación es una estrategia de inversión que consiste en repartir el capital entre diferentes activos financieros para reducir el riesgo. Como dice el refrán: 'no pongas todos los huevos en una canasta'. La teoría moderna de portafolios de Harry Markowitz formalizó este concepto."
            elif 'riesgo' in message_lower and 'retorno' in message_lower:
                return "⚖️ La relación riesgo-retorno es un principio fundamental de las finanzas: para obtener mayores retornos esperados, los inversores deben aceptar asumir mayores niveles de riesgo. Esta relación no es lineal y varía según el perfil de riesgo de cada individuo."
            elif 'liquidez' in message_lower:
                return "💧 La liquidez se refiere a la facilidad con que un activo puede convertirse en efectivo sin perder valor significativo. Los activos líquidos (como el efectivo o acciones de empresas grandes) se pueden vender rápidamente, mientras que los ilíquidos (como bienes raíces) tardan más tiempo en venderse."
            elif 'volatilidad' in message_lower:
                return "📊 La volatilidad mide la variabilidad de los precios de un activo financiero a lo largo del tiempo. Una alta volatilidad significa que los precios fluctúan mucho, lo que implica mayor riesgo pero también potencial de mayores retornos."
            elif 'valor presente' in message_lower:
                return "⏰ El valor presente es el concepto de que un dólar hoy vale más que un dólar en el futuro debido al potencial de ganancia que tiene el dinero. Se calcula descontando el valor futuro usando una tasa de descuento que refleja el costo de oportunidad del capital."
            elif 'mercado primario' in message_lower:
                return "🏛️ El mercado primario es donde se emiten y venden valores financieros por primera vez. Aquí las empresas y gobiernos obtienen financiamiento directamente de los inversores mediante la emisión de acciones, bonos u otros instrumentos."
            elif 'mercado secundario' in message_lower:
                return "🔄 El mercado secundario es donde se negocian valores financieros que ya han sido emitidos anteriormente. Aquí los inversores compran y venden entre sí, proporcionando liquidez al mercado sin generar nuevos fondos para las empresas emisoras."

        # Preguntas sobre impuestos y fiscalidad
        elif any(word in message_lower for word in ['impuesto', 'iva', 'fiscal', 'declaracion', 'renta', 'tax', 'tributo']):
            impuestos_responses = [
                "📋 Estrategias fiscales: Optimiza tus impuestos usando deducciones legítimas y planificación anual. En muchos países, invertir en educación o vivienda ofrece beneficios fiscales atractivos. ¿Quieres que revisemos tus oportunidades de ahorro fiscal?",
                "💼 Impuestos sobre inversiones: Las ganancias de capital tienen tratamientos fiscales favorables en la mayoría de jurisdicciones. El 'impuesto a la riqueza' es tema de debate global. ¿Te ayudo a entender tu situación fiscal específica?",
                "🏦 Planificación fiscal internacional: La movilidad de capital permite optimizar cargas fiscales. Paraísos fiscales legítimos existen, pero la transparencia es clave. ¿Interesado en estrategias de diversificación fiscal?",
                "📊 IVA y consumo: Los impuestos al consumo afectan directamente tu poder adquisitivo. Comprender la estructura tributaria te ayuda a tomar mejores decisiones de gasto. ¿Quieres análisis de tu estructura fiscal?",
                "🎯 Deducciones fiscales: Educación, salud, vivienda y donaciones ofrecen deducciones en la mayoría de sistemas fiscales. Planificar con anticipación maximiza beneficios. ¿Revisamos tus deducciones disponibles?"
            ]
            return random.choice(impuestos_responses)

        # Respuestas por defecto con opciones claras (mejorado)
        else:
            respuestas_default = [
                f"¡Buena curiosidad! 🤔 Para darte la mejor respuesta sobre '{message}', ¿podrías indicarme a cuál de los **cuatro pilares de tu plan '{plan.nombre}'** te refieres? 1) **Optimización de Gastos**, 2) **Estrategias de Ahorro**, 3) **Progreso de Objetivos** o 4) **Inversiones**.",
                f"¡Qué interesante consulta! 💭 Sobre '{message}'... Tengo conocimientos en economía conductual, mercados financieros y estrategias de inversión. ¿Quieres que hablemos de gastos, ahorro, objetivos, o prefieres un análisis más profundo de tu **perfil de riesgo**?",
                f"¡Me encanta que preguntes! 🌟 '{message}' es un tema fascinante. Mi expertise incluye análisis de presupuestos, evaluación de riesgos y planificación financiera. ¿Podrías decirme si te refieres a tus gastos, ahorro, objetivos, o necesitas un **consejo macroeconómico**?",
                f"¡Excelente curiosidad! 🔍 '{message}'... Puedo abordar esto desde ángulos como: microeconomía personal, diversificación de inversiones, o psicología financiera. ¿Qué aspecto te interesa más explorar?"
            ]
            return random.choice(respuestas_default)

    except Exception as e:
        # Respuesta de error más robusta y útil
        return f"Lo siento, tuve un problema accediendo a tus datos financieros. Esto suele pasar si falta algún dato clave (ej. no has ingresado ningún gasto todavía). Error: {str(e)}. Por favor, verifica la integridad de tus datos en el plan '{plan.nombre}'."