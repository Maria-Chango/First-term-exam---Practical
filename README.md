Proyecto FastAPI: Análisis de Vulnerabilidad por Fuerza Bruta
Índice
-Introducción y Propósito
-Stack Tecnológico
-Configuración del Entorno
-Demostración de Ataque
-Análisis de Resultados
-Conclusiones de Seguridad y Mitigación

1. Introducción y Propósito
Este proyecto implementa una API REST de gestión de usuarios.El propósito principal es demostrar la criticidad de la vulnerabilidad de credenciales débiles.

Utilizamos un script de fuerza bruta personalizado para atacar el endpoint de login y exponer la facilidad con la que un atacante puede comprometer una cuenta con una contraseña común.

2. Stack Tecnológico
Componente	/// Tecnología      ///   Función
Framework----FastAPI----------------Core de la API.
Seguridad----Passlib (bcrypt)-------Hashing seguro de contraseñas.
Pruebas------Bash / cURL / xargs----Script de ataque cliente.
Datos--------Pydantic--------------Validacion de esquemas y tipado de datos.
Entorno------Python 3.[X]----------Entorno de ejecución.


🚧 Usuario de Prueba para el Ataque
La API se inicializa con el siguiente usuario vulnerable para las pruebas:

Usuario: tester_brute
Contraseña: 123456 (Vulnerable)

3. Configuración del Entorno

3.1. Requisitos e Instalación
Bash
# 1. Asegúrarse de tener Python y Git Bash o WSL instalados.
# 2. Instalar las dependencias necesarias:
pip install fastapi uvicorn 'passlib[bcrypt]'

3.2. Ejecución del Servidor
El servidor debe estar activo para que el ataque funcione.

Bash
uvicorn main:app --reload
La documentación de la API está disponible en: http://127.0.0.1:8000/docs

4. Demostración de Ataque
El archivo brute_force_test.sh ejecuta el ataque, iterando sobre el diccionario passwords.txt.

4.1. Ejecución del Script (Terminal Secundaria)
Bash

./brute_force_test.sh

4.2. Detrás de Escena: La Lógica Compleja del Script
Este script es intencionalmente complejo debido al troubleshooting en entornos Windows/MINGW64.

Uso de xargs y bash -c: Se utiliza para forzar la ejecución de curl por cada línea del diccionario. Esto fue necesario porque el entorno de Git Bash fallaba al ejecutar el bucle while read estándar, demostrando una limitación en la portabilidad de los scripts Bash.

Archivos Temporales (attempts.tmp): Se utilizan para contar los intentos y la señal de éxito, ya que el subproceso generado por xargs no puede comunicar directamente sus variables al script principal.

5. Análisis de Resultados
El ataque fue un éxito rotundo, como se confirma en el archivo brute_force_results.log y en los logs del servidor.

Métrica	-------------Valor -----------------    Observación
Credencial 
Comprometida	tester_brute:123456	   Confirmado por el 200 OK en el log del servidor.

Intentos 
Necesarios	           6	          La contraseña se encontró en el sexto intento.

Vulnerabilidad	Ausencia de Mitigación	El endpoint respondió al intento 1 y al intento 6.


6. Conclusiones de Seguridad y Mitigación

La prueba confirma que una contraseña débil, en un entorno sin defensa, resulta en un compromiso instantáneo de la cuenta.

🔴 Riesgo Principal: Cuentas Comprometidas
La debilidad principal del sistema es la falta de cualquier mecanismo de defensa proactivo. El servidor asume que todos los intentos fallidos son legítimos y procesa la petición de forma instantánea.

✅ Estrategias de Mitigación Recomendadas
Para asegurar el endpoint /login, se deben implementar las siguientes medidas:

Rate Limiting (Control de Tasa):

Limitar los intentos de inicio de sesión por dirección IP o por usuario a 5-10 peticiones por minuto. Esto haría que el ataque de fuerza bruta sea inviable en términos de tiempo.

Políticas de Contraseñas Fuertes:

Aumentar la validación Pydantic (UserCreate) para exigir una longitud mínima de 12 caracteres y la inclusión de mayúsculas, minúsculas, números y símbolos.

Bloqueo de Cuentas (Account Lockout):

Bloquear temporalmente la cuenta de un usuario (ej., por 15 minutos) después de 5 intentos fallidos consecutivos, forzando al atacante a cambiar de objetivo.