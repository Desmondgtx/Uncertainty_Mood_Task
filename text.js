
  var html_form = `<div class="contactform">
  <form method="post" action="#" name="contact" class="needs-validation" id="main_form">
    <h1>EXPERIMENTO</h1>
  <fieldset>
      <legend> <b>INFORMACIÓN PERSONAL</b></legend>
      <p>
      <label for="fname"><b>Nombre</b> </label>
      <br>
      <input class="form-control" type="text" id="fname" name="firstname" placeholder="Ingresa tu nombre..." required /></p>
      <p>
      <label for="lname"><b>Apellido</b> </label>
      <br>
      <input class="form-control" type="text" id="lname" name="lasttname" placeholder="Ingresa ambos apellidos..." required /></p>
      <p>
      <label for="email"><b>Correo</b> </label>
      <br>
      <input class="form-control" type="text" id="email" name="email-contact" placeholder="Ingrese su correo electronico." required /></p>
              <p>
                  <b>Genero</b>
                  <br><br>
                  <input class="form-control" type="radio" name="gen" id="fem" value="fem" required>
                  <label for="fem"> Femenino </label>
                  <br>
                  <input class="form-control" type="radio" name="gen" id="mas" value="mas" required>
                  <label for="mas"> Masculino </label>
                  <br>
                  <input class="form-control" type="radio" name="gen" id="nob" value="nob" required>
                  <label for="nob"> No binario </label>
                  <br>
                  <input class="form-control" type="radio" name="gen" id="nor" value="nor" required>
                  <label for="nor"> No Responde </label>
                  <br>
              </p>
              <p>
                  <b>Lateralidad <small>       (¿zurdo o diestro?)</small> </b>
                  <br><br>
                  <input class="form-control" type="radio" name="lat" id="der" value="der" required>
                  <label for="der"> Derecha </label>
                  <br>
                  <input class="form-control" type="radio" name="lat" id="izq" value="izq" required>
                  <label for="izq"> Izquierda </label>
                  <br><br>
              </p>
                  <label for="age"><b>Edad</b></label>
                  <br><br>
                  <select name="age" id="age" required>
                          <option>18</option>
                          <option>19</option>
                          <option>20</option>
                          <option>21</option>
                          <option>22</option>
                          <option>23</option>
                          <option>24</option>
                          <option>25</option>
                          <option>26</option>
                          <option>27</option>
                          <option>28</option>
                          <option>29</option>
                          <option>30</option>
                          <option>31</option>
                          <option>32</option>
                          <option>33</option>
                          <option>34</option>
                          <option>35</option>
                          <option>36</option>
                          <option>37</option>
                          <option>38</option>
                          <option>39</option>
                          <option>40</option>                      
                  </select>
              </p> 
  </fieldset><br>
  <br><fieldset>
          <legend><b>CONSENTIMIENTO INFORMADO</b></legend>
              <p id="consent"><br><br></p>
          <button type="buton" class="btn btn-success">ACEPTAR</button>
  </fieldset>
  </form>
  </div>`
  
  var informed_consent = 
  "declaro que he sido informado e invitado a participar en una investigación \
  denominada “Cognitive Model for Uncertainty”, éste es un proyecto de investigación \
  científica que cuenta con el respaldo y financiamiento de la ANID.\
  <br><br>Esta investigación está a cargo de Miguel Fuentes, y tiene como co-investigadores \
  al docente Claudio Lavín Tapia y Roberto Garcia. \
  <br><br>Entiendo que este estudio busca conocer identificar la forma en que las personas \
  toman decisiones en contexto de incertidumbre y los procesos cognitivos asociados \
  a esta toma de decisiones.\
  <br><br>Sé que mi participación se llevará a cabo en el horario a definir con quien \
  realice la toma de los datos y consistirá en participar de una tarea experimental \
  y cuestionario una encuesta, donde el proceso completo demorará alrededor de 1 hora. \
  <br> Me han explicado que la información registrada será confidencial, \
  y que los nombres de los participantes no serán publicados, esto significa que  \
  las respuestas no podrán ser conocidas por otras personas ni tampoco ser identificadas \
  en la fase de publicación de resultados.\
  <br><br>Estoy en conocimiento que los datos no me serán entregados aunque sí habrá una \
  retroalimentación general de los resultados del estudio, y sé que esta información \
  podrá beneficiar de manera indirecta y por lo tanto tiene un beneficio para la sociedad \
  dada la investigación que se está llevando a cabo.\
  <br><br>Asimismo, sé que puedo negar la participación o retirarme en cualquier etapa de la \
  investigación, sin expresión de causa ni consecuencias negativas para mí.\
  <br><br>Sí. Acepto voluntariamente participar en este estudio y he recibido una copia del presente documento.\
  vSi tiene alguna pregunta durante cualquier etapa del estudio puede comunicarse con el investigador \
  responsable (Claudio Lavín), puede hacerlo al número +56968512716 o al correo claudio.lavin@gmail.com\
  <br><br><br> <b> HE TENIDO LA OPORTUNIDAD DE LEER ESTA DECLARACIÓN DE CONSENTIMIENTO INFORMADO, \
  <br><br><br> HACER PREGUNTAS ACERCA DEL PROYECTO DE INVESTIGACIÓN, Y ACEPTO PARTICIPAR EN ESTE PROYECTO.</b>\
  <br><br>";
  

var prompt_instructions = ["<pre> Anterior [&#8592;]                                  Siguiente [&#8594;]</pre>",
"<pre> Anterior [&#8592;]                                  Siguiente [&#8594;]</pre>",
"<pre> Anterior [&#8592;]                                Comenzar [Enter]</pre>"]

var prompt_pause = ["<pre>                   Continuar [Enter]</pre>"];

var task_images = ['img/choice1.png','','img/choice2.png'];

var task_pages = ["A continuacion apareceran una serie de pares de simbolos, \
uno a la derecha y otro a la izquierda de la pantalla. \
Para elegir un simbolo, debe mover la marca azul. \
Utilize las fechas izquierda y derecha del teclado \
para elegir un simbolo. \
Utilize la barra espaciadora para confirmar la elección.",

"Luego de cada elección se le solicitara indicar \
la confianza que tiene en que su respuesta es correcta. \
Para esto, utilice las flechas a la derecha o izquierda  \
para deslizar la barra entre el 0% y el 100%. \
Utilize la barra espaciadora para confirmar la elección. \
Al finalizar cada decision, se le entregara retroalimentación \
CORRECTO o INCORRECTO, y se presentara un nuevo par de simbolos.",

"Su objetivo es encontrar para cada par de simbolos, \
el mejor de ellos. \
Pero tenga cuidado. No existe un simbolo que SIEMPRE \
sea mejor que otro, pero si existen simbolos que son \
mejores LA MAYOR PARTE DEL TIEMPO. \
Para descubrir cuales son, debe aprender por ENSAYO Y \
ERROR cual es el mejor LA MAYORIA de las veces."]

var end_msg = "<p class=\"large\"> <b>El experimento ha finalizado. </b></p>" +
              "<p class=\"large\"> Muchas gracias por participar.</p>";

var msg_pausa = "<p class=\"large\"> <b>PAUSA </b></p>" +
"<p class=\"large\"> Tome un breve momento para descansar.</p>"

var msg_mid ='<p style="font-size:20px; color:black;"> <b>LLEVAS MAS DE LA MITAD COMPLETADA!</b> </p>'+
"<p class=\"large\"> Tome un breve momento para descansar.</p>"

var prompt_cont = "<p class=\"large\"> Presione la tecla <b>ESPACIO</b> para continuar.</p>";
