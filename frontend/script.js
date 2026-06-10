const cameraBtn = document.getElementById("cameraBtn");
const cameraInput = document.getElementById("cameraInput");
const previewImagem = document.getElementById("previewImagem");
const placeholderFoto = document.getElementById("placeholderFoto");
const textoLeitura = document.getElementById("textoLeitura");
const botao = document.getElementById("playPauseBtn");





console.log("SCRIPT CARREGADO");

cameraBtn.addEventListener("click", () => {
    console.log("BOTAO CLICADO");
    cameraInput.click();
});

cameraInput.addEventListener("change", () => {
    console.log("ARQUIVO ESCOLHIDO");
});





let velocidadeAtual = 1;
let falando = false;
let pausado = false;

cameraInput.addEventListener("change", async function () {

   const arquivo = this.files[0];

   if (!arquivo) return;

   const nome = arquivo.name.toLowerCase();

   if (
      !arquivo.type.startsWith("image/") &&
      !nome.endsWith(".pdf")
   ) {
      alert("Arquivo inválido");
      return;
   }

   console.log("Arquivo:", arquivo);
   console.log("Tipo:", arquivo.type);
   console.log("Tamanho:", arquivo.size);

   // Preview imagem escolhida
   if (arquivo.type.startsWith("image/")) {
      previewImagem.src = URL.createObjectURL(arquivo);
      previewImagem.style.display = "block";
   } else {
      previewImagem.style.display = "none";
   }

   placeholderFoto.style.display = "none";

   // Loading de transcrição
   textoLeitura.innerText = "Transcrevendo imagem...";

   try {
      const formData = new FormData();
      formData.append("file", arquivo);

      console.log("Enviando para:", `${API_BASE_URL}/ocr_google`);

      const resposta = await fetch(`${API_BASE_URL}/ocr_google`, {
         method: "POST",
         body: formData
      });

      console.log("STATUS:", resposta.status);

      if (!resposta.ok) {
         throw new Error("Erro na requisição OCR.");
      }

      const dados = await resposta.json();

      if (dados.error) {
         throw new Error(dados.error);
      }

      let transcricao = dados.texto;

      if (dados.audio) {
         const audioPlayer = new Audio("data:audio/mp3;base64," + dados.audio);
         audioPlayer.play().catch(err => {
            console.log("Safari bloqueou autoplay:", err);
         });
      }

      textoLeitura.innerText = transcricao;
      iniciarLeituraAutomatica(transcricao);
   } catch (erro) {

   console.error("ERRO COMPLETO:", erro);

   textoLeitura.innerText =
   "Erro: " + erro.message;
}
});

/* CONTROLE DE VELOCIDADE */
document
.getElementById("speedControl")
.addEventListener("change", function () {

   velocidadeAtual =
   parseFloat(this.value);

});



/* LEITURA AUTOMÁTICA APÓS OCR */
function iniciarLeituraAutomatica(texto){

   speechSynthesis.cancel();

   let fala = new SpeechSynthesisUtterance(texto);

   fala.lang = "pt-BR";
   fala.rate = velocidadeAtual;

   fala.onstart = function(){
      falando = true;
      pausado = false;
      botao.innerHTML = "❚❚";
   };

   fala.onend = function(){
      falando = false;
      pausado = false;
      botao.innerHTML = "▶";
   };

   const vozes = speechSynthesis.getVoices();

   const vozPT = vozes.find(
      v => v.lang.includes("pt")
   );

   if (vozPT){
      fala.voice = vozPT;
   }

   speechSynthesis.speak(fala);
}


/* PLAY / PAUSE / CONTINUAR */
function controlarLeitura(){

   // continuar
   if(pausado){

      speechSynthesis.resume();

      pausado = false;

      falando = true;

      botao.innerHTML = "❚❚";

      return;
   }


   // pausar
   if(falando){

      speechSynthesis.pause();

      pausado = true;

      falando = false;

      botao.innerHTML = "▶";

      return;
   }


   // iniciar manualmente
   let texto =
   document.getElementById("textoLeitura").innerText;

   iniciarLeituraAutomatica(texto);

}



/* CONTROLES FUTUROS */
function voltarTexto(){

   alert("Voltar trecho");

}


function avancarTexto(){

   alert("Avançar trecho");

}

window.controlarLeitura = controlarLeitura;
window.voltarTexto = voltarTexto;
window.avancarTexto = avancarTexto;