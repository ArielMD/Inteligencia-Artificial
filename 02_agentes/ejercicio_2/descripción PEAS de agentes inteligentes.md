### 1. Asistente virtual de voz (Siri)

- **Performance:** Tiempo de respuesta para una actividad especifica y su completitud. Consultar información de la web debe ser especifica y confiable. Realizar una actividad que genere un recurso como crear un recordatorio.

Rapidez, completitud, caridad
- **Environment:** Actividad cotidianas de humano, dispositivo, necesita conexión a internet mediante wifi/datos móviles

|Tipo de ambiente| Asistente virtual de voz (Siri)|
|--|--|
|Observable| **Parcialmente observable**, el asistente no tiene toda la información del usuario  solamente a los permitidos|
|Estocástico| **Estocástico** la consulta a internet no siempre será la misma. Agendar una actividad puede ser el mismo día, pero no el mismo tiempo|
|Episódico| **Secuencial** Una solicitud puede afectar recurso como agendar un recordatorio, ya que se crea un recurso que puede usar en futuras solicitudes |
|Estático| **Dinámico** No se detiene todo el dispositivo hasta que se procese una solicitud de asistente|
|Discreto| **Continue** Si las instrucciones se hacen con voz|


- **Actuators:** Altavoz y pantalla para mostrar notificaciones/resultados, API para crear recursos en las apps del dispositivo.
- **Sensors:** Micrófono, GPS, API para consultar datos a apps del dispositivo.

### 2. Robot aspirador doméstico

- **Performance:** Tiempo de aspirado entre el total área a limpiar debe ser consistente y debe elegir el camino mas optimo para no repetir la trayectoria. y cubrir el área total hasta que detecte la mínima cantidad de partículas permitidas.
- **Environment:** Forma del área a limpiar de la casa/oficina. La cantidad de seres vivos en el área, obstáculos, suciedad y duración de batería.

|Tipo de ambiente| Robot aspirador doméstico|
|--|--|
|Observable| **Parcialmente observable** No puede tener una percepción total de los elementos del área a limpiar, la forma puede ser fija pero muebles, objetos puede moverse durante el día y los sensores de proximidad tienen un limite de alcance|
|Estocástico| **Estocástico** Los elementos se puede mover de lugar y no siempre se puede usar el mismo camino de días anteriores|
|Episódico| **Secuencial**  Cada limpieza puede ser diferente cada día, el nivel de suciedad puede necesitar mas pasadas del robot y debe encontrar el camino mas optimo para el área, al moverse puede |
|Estatico| **Dinámico** | El ambiente puede cambiar mientras en robot está en funcionamiento, lo puede mover de posición, agregar un objeto que no estaba anteriormente en la primera pasada.
|Discreto| **Continue** | Puede varias la velocidad de los motores para moverse y de las aspas. Se puede mover rápido en lugares con poca suciedad y lento en lugares con alta suciedad.

- **Actuators:** API para app del usuario para mostrar la información del aspirador y de la limpieza.
- **Sensors:** GPS, sensor de proximidad, sensor infrarrojo


### 3. Sistema de recomendación de streaming (Netflix)

- **Performance:** El usuario interactuó con las recomendaciones, leyó alguna descripción de una serie/película, lo agrego a su lista, minutos vistos del total de tiempo de las recomendaciones. 
- **Environment:** Dispositivo del usuario móvil/pc/tablet, ubicación del usuario y su conexión a internet. Preferencia, historial de navegación, calificaciones y películas/series vistas, catalogo de la app.

|Tipo de ambiente| Sistema de recomendación de streaming (Netflix)|
|--|--|
|Observable| **Parcialmente observable**No se puede conocer los gustos, ánimos del usuario, ya que estos pueden cambiar por aspectos diarios  |
|Estocástico| **Estocástico** Cambios en su historial de búsqueda, ánimos, y preferencia puede cambiar la percepción de las recomendaciones|
|Episódico| **Secuencial**  Las series/películas vistas, las calificaciones dadas pueden afectar futuras recomendaciones|
|Estático| **Dinámico** El ambiente, las películas/series se agregan/remueven cada cierto tiempo películas/series del catalogo y los gustos de usuario no siempre será el mismo|
|Discreto| **Discreto** Se tiene un limite de opciones que se puede elegir en el catalogo|
- **Actuators:** Lista de recomendaciones en el perfil del usuario
- **Sensors:** Historial de búsqueda, películas vistas, calificación/genero 


### 4. Vehículo autónomo en ciudad

- **Performance:** Confiabilidad, Seguridad, ruta mas optima de acuerdo al trafico y distancia, puntuación de conducción que tan brusco se mantiene el carro en la calle.
- **Environment:** Calles de Mérida con señalamientos y marcas poco claros, cantidad de baches y calles angostas.

|Tipo de ambiente| Vehículo autónomo en ciudad |
|--|--|
|Observable| **Parcialmente observable**, No se puede conocer la calidad de las calles, el trafico exacto y eventos que pueden afectar la ruta establecida|
|Estocástico| **Estocástico** No se puede predecir con certeza el trafico o conductores que puedan provocar un accidente|
|Episódico| **Secuencial**  Las decisiones de la ruta, la velocidad afecta a la ruta establecida |
|Estático| **Dinámico** El tiempo pasa el ambiente no se detiene y en cada vez se tiene que calcular las decisiones|
|Discreto| **Continue** Puede haber variaciones en la velocidad del carro acelerar para rebasar o detenerse en un alto y velocidad de giro|
- **Actuators:** Motores, direccional, luces 
- **Sensors:** Sensores de proximidad, GPS, giroscopio para inclinación, cámaras 


### 5. Agente de trading algorítmico en bolsa 

- **Performance:** (Ganancia final - monto inicial) / N. Movimientos en bolsa. Obtener ganancia en el menor números de movimientos. 
- **Environment:** Dispositivo, un broker, conexión a internet para noticias, inversiones y conflictos en el mundo

|Tipo de ambiente| Agente de trading algorítmico en bolsa |
|--|--|
|Observable| **Parcialmente observable** No es posible conocer todas las variables que impactan al mercado ni los movimientos de las grandes empresas que tienen información privilegiada |
|Estocástico| **Estocástico** Cada accion de compra y venta va cambiando en cada momento de acuerdo al mercado y un movimiento no siempre tendra el mismo resultado|
|Episódico| **Secuencial**  Cada moviento realizado puede afectar a los próximos, si una venta te produce ganancias eso afecta a cuantas acciones podras comprar a futuro disminuyendo tus ganancias|
|Estático| **Dinámico** mientras el agente toma una decisión el mercado va cambiando, una decisión tardía puede producirte entrar cuando el precio ya subió|
|Discreto| **Continuo** El precio fluctúa  |
- **Actuators:** Api para ejecutar acciones de compra/venta
- **Sensors:** Paginas web de noticias, redes sociales, api para consultar datos en tiempo real del broker

### 6. Sistema de diagnóstico médico asistido por IA 

- **Performance:** Dar un diagnostico de acuerdo a los síntomas del paciente con un porcentaje de confianza alto (95%), coincida con la hipotesis del doctor. 
- **Environment:** Historial clínico del paciente, síntomas actuales y aspectos físicos del paciente.

|Tipo de ambiente| Sistema de diagnóstico médico asistido por IA |
|--|--|
|Observable| **Parcialmente observable** se puede conocer los síntomas del paciente dice y se complementa fisicamente, pero hay enfermedades asintomáticas que no pueden ser descritas|
|Estocástico| **Determinista** la mayoría de las enfermedades son de causa/efecto si suelen ser iguales para la mayoría de las personas siempre y cuando se conozca que lo causa|
|Episódico| **Episódico** Cada paciente tiene diferentes síntomas y el resultado varia de acuerdo al paciente diagnosticado |
|Estático| **Dinámico** Las enfermedades se desarrollan mientras pasa el tiempo, algunas puede presentar síntomas adicionales |
|Discreto| **Continue**  porque las enfermedades evolucionan con el tiempo|
- **Actuators:** Api para ejecutar acciones de compra/venta
- **Sensors:** Paginas web de noticias, redes sociales, api para consultar datos en tiempo real del broker


### 7. Dron de inspección de infraestructura

- **Performance:** Comparar el tiempo de inspección, fallas encontradas en cada inspección vs una inspección humana
- **Environment:** Zonas de riesgo, altitud, fuertes vientos, clima, zonas estrechas y trabajo a grandes distancias.

|Tipo de ambiente| Dron de inspección de infraestructura|
|--|--|
|Observable| **Parcialmente observable** el dron solo puede observar con los sensores equipados, puede haber otros fallas en una infraestructura que el dron no esta preparado |
|Estocástico| **Estocástico** En una inspección se planea una ruta, donde se debe buscar la rutas mas optima para que el dron inspección, obtenga la mayor cantidad de información puede regresar |
|Episódico| **Secuencial** cada acción realiza el dron afecta a su posición y desgasta el tiempo operativo |
|Estático| **Dinámico** porque la infraestructura puede cambiar si esta en funcionamiento, aspectos como el viento, cambios en el clima siempre esta presentes|
|Discreto| **Continue** porque influye la posición que puede tener el dron, velocidad y viento|
- **Actuators:** motores, envío de fallas encontradas y datos en tiempo real.
- **Sensors:** Acelerómetro, sensores de proximidad, sensores de infrarrojo, temperatura, micrófono, sensores electrostáticos, cámaras.


### 8. Agente jugador de ajedrez 

- **Performance:** Ganar la partida con el menor movimiento con movimientos validos, si ganas 1, tablas 0 y si pierdes -1 
- **Environment:** Tablero y reglas oficiales del ajedrez, movimientos históricos de los jugadores
|Tipo de ambiente| Agente jugador de ajedrez |
|--|--|
|Observable| **observable**, las posición de las piezas de ajedrez son visibles para los jugadores |
|Estocástico| **Determinista** los movimientos están definidos por las reglas del ajedrez|
|Episódico| **Secuencial** los movimientos cambian el tablero y las desiciones futuras del jugador|
|Estático| **Dinámico** al cambiar el tablero|
|Discreto| **Discreto** se tiene un limite de combinaciones de las posiciones de las piezas en el ajedrez |
- **Actuators:** Mover una pieza en un movimiento valido
- **Sensors:** Tablero actual, movimientos realizadas y a que jugador le toca mover las piezas



