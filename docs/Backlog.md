# 📝 Notes.
- [ ] Hay que traducir en la respuesta del LLM los terminos asociados a Battleship a terminologia de Logistica.
    - SUNK -> Pedido Encajado.
    - HIT -> Prenda encajada. 
    - MISS -> Prenda perdida.
- [ ]  Tiro forzado debería ser random pero excluyendo las coordenadas que ya han sido atacadas.
- [ ] Intentar fijar el tamaño de la pantalla del terminal para que no se rompa el formato. 
- ⚠️ Posible cambio de estrategia: 
    - Los equipos programaran un modulo en python (Brain.py)que se encargue de decidir la estrategia
    - El modulo puede consultar a la IA cada 10 turnos.
    - Se le pasa el historial completo de los (miss,hit y sunk) y la IA devolvería cuandrante a atacar.

- [ ] El sleep de 5 segundos igual no es necesario segun los tiempo de la última partida.
- [ ] Comprimir la información de celdas prohibidas agrupadas por miss, hit y sunk.