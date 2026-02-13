#Rivera Buenrostro Aram Elias
#Vazquez Morales Ivan
#Grupo: 7CV11
#Teoria de la Informacion y Codificacion 

from pydoc import text
import sys
from typing import Self
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QTextEdit, QLabel,
                             QStackedWidget, QFileDialog, QMessageBox, QRadioButton, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pyaudio
import threading
from PIL import Image
import os
import math
from collections import Counter

# ----------------- FUNCIÓN DE ENTROPÍA CON TABLA -----------------
def calcular_entropia_con_tabla(datos):
    if datos is None:
        return 0, "No hay datos", 0
    
    # Convertir a lista según tipo
    try:
        if isinstance(datos, str):
            elementos = list(datos)
        elif isinstance(datos, (bytes, bytearray)):
            elementos = list(datos)
        elif isinstance(datos, np.ndarray):
            # Para arrays de NumPy, asegurar que sea 1D
            if datos.size == 0:
                return 0, "Array vacío", 0
            elementos = datos.flatten().tolist()
        elif isinstance(datos, list):
            elementos = datos
        else:
            try:
                elementos = list(datos)
            except:
                return 0, "Tipo de datos no soportado", 0
    except:
        return 0, "Error al procesar datos", 0
    
    N = len(elementos)
    if N == 0:
        return 0, "No hay datos", 0
    
    frecuencias = Counter(elementos)
    
    linea = "=" * 100
    tabla = f"\n{linea}\n"
    tabla += f"| {'Símbolo (x_i)':<25} | {'Frecuencia F_i':<15} | {'Probabilidad p(x_i)':<25} | {'p(x_i) log2(1/p(x_i))':<25} |\n"
    tabla += f"{linea}\n"
    
    suma_entropia = 0.0
    items = sorted(frecuencias.items(), key=lambda x: x[1], reverse=True)
    
    # Limitar a 50 filas para no saturar
    for simbolo, freq in items[:50]:
        prob = freq / N
        contrib = prob * math.log2(1/prob) if prob > 0 else 0
        suma_entropia += contrib
        
        # Formatear símbolo
        if isinstance(simbolo, str):
            if simbolo == '\n':
                sym_str = '\\n'
            elif simbolo == '\t':
                sym_str = '\\t'
            elif simbolo == ' ':
                sym_str = '␣'
            else:
                sym_str = simbolo if len(simbolo) < 15 else simbolo[:12] + '...'
        else:
            sym_str = str(simbolo)
        
        tabla += f"| {sym_str:<25} | {freq:<15} | {prob:<25.8f} | {contrib:<25.8f} |\n"
    
    if len(items) > 50:
        tabla += f"| {'... y ' + str(len(items)-50) + ' más':<25} | {'...':<15} | {'...':<25} | {'...':<25} |\n"
    
    tabla += f"{linea}\n"
    tabla += f"| {'Número total de símbolos:':<25} | {N:<15} | {'Entropía H:':<25} | {suma_entropia:<25.8f} |\n"
    tabla += f"{linea}\n"
    
    return suma_entropia, tabla, N
# ----------------- Grabadora de Voz -----------------
class VoiceRecorder:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.is_recording = False
        self.stream = None
        
    def start_recording(self):
        self.frames = []
        self.is_recording = True
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                     channels=1,
                                     rate=44100,
                                     input=True,
                                     frames_per_buffer=1024)
        def record():
            while self.is_recording:
                try:
                    data = self.stream.read(1024, exception_on_overflow=False)
                    self.frames.append(data)
                except:
                    break
        self.recording_thread = threading.Thread(target=record)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
    def stop_recording(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

# ----------------- Pantalla de Bienvenida -----------------
class WelcomeScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        title = QLabel("ANALIZADOR DE ARCHIVOS DE TEXTO, AUDIO E IMAGENES CON ENTROPIA")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold; margin: 30px;")
        layout.addWidget(title)

        autores_info = "Proyecto de Teoría de la Información y Codificación\n\nCreadores:\n- Rivera Buenrostro Aram Elias \n- Vazquez Morales Ivan \n-7CV11"
        autores = QLabel(autores_info)
        autores.setAlignment(Qt.AlignCenter)
        autores.setStyleSheet("font-size: 16px; color: #555; margin-bottom: 40px;")
        layout.addWidget(autores)

        start_btn = QPushButton("INICIAR APLICACIÓN")
        start_btn.clicked.connect(self.start_application)
        start_btn.setStyleSheet("padding: 15px; font-size: 18px; background-color: #27ae60; color: white; border-radius: 10px;")
        layout.addWidget(start_btn)
        self.setLayout(layout)
    
    def start_application(self):
        self.main_window.show_main_interface()

# ----------------- Analizador de Texto -----------------
class TextAnalyzerWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Escribe tu texto aquí o sube un archivo .txt...")
        layout.addWidget(self.text_edit)
        buttons_layout = QHBoxLayout()
        upload_btn = QPushButton("Subir Archivo .txt")
        upload_btn.clicked.connect(self.upload_text_file)
        buttons_layout.addWidget(upload_btn)
        analyze_btn = QPushButton("Analizar Texto")
        analyze_btn.clicked.connect(self.analyze_text)
        buttons_layout.addWidget(analyze_btn)
        entropy_btn = QPushButton("📊 Mostrar Tabla de Entropía")
        entropy_btn.clicked.connect(self.mostrar_tabla_entropia_texto)
        buttons_layout.addWidget(entropy_btn)
        layout.addLayout(buttons_layout)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)
        self.setLayout(layout)
    
    def upload_text_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo de Texto", "", "Archivos de texto (*.txt)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.text_edit.setText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def analyze_text(self):
        text = self.text_edit.toPlainText().lower()
        if not text:
            self.result_text.setText("Escribe o carga un texto primero")
            return
        words = text.split()
        letters = {}
        for c in text.replace(" ", ""):
            if c.isalpha():
                letters[c] = letters.get(c, 0) + 1
        sentences = text.count('.') + text.count('!') + text.count('?')
        result = f"Palabras: {len(words)}\nCaracteres: {len(text)}\nCaracteres sin espacios: {len(text.replace(' ','') )}\n"
        for k, v in sorted(letters.items()):
            result += f"{k}: {v}\n"
        self.result_text.setText(result)
    
    def mostrar_tabla_entropia_texto(self):
        text = self.text_edit.toPlainText()
        if not text:
            QMessageBox.warning(self, "Advertencia", "No hay texto para analizar")
            return
        
        entropia, tabla, N = calcular_entropia_con_tabla(text)
        resultado = f"""
=== TABLA DE ENTROPÍA DE SHANNON - TEXTO ===
Entropía total: {entropia:.4f} bits
Total de símbolos: {N}
{tabla}
"""
        self.result_text.setText(resultado)

# ----------------- Grabadora de Voz Widget -----------------
class VoiceRecorderWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.recorder = VoiceRecorder()
        layout = QVBoxLayout()
        self.record_btn = QPushButton("🎤 Iniciar Grabación")
        self.record_btn.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_btn)
        
        self.entropy_btn = QPushButton("📊 Mostrar Tabla de Entropía")
        self.entropy_btn.clicked.connect(self.mostrar_tabla_entropia_audio)
        self.entropy_btn.setEnabled(False)
        layout.addWidget(self.entropy_btn)
        
        self.figure = Figure(figsize=(5,2))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.ax = self.figure.add_subplot(111)
        self.line, = self.ax.plot([])
        self.ax.set_ylim(-32768,32767)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.setLayout(layout)
    
    def toggle_recording(self):
        if not self.recorder.is_recording:
            self.recorder.frames = []
            self.recorder.start_recording()
            self.record_btn.setText("⏹️ Detener Grabación")
            self.timer.start(100)
            self.entropy_btn.setEnabled(False)
        else:
            self.recorder.stop_recording()
            self.record_btn.setText("🎤 Iniciar Grabación")
            self.timer.stop()
            if len(self.recorder.frames) > 0:
                self.entropy_btn.setEnabled(True)
    
    def update_plot(self):
        if self.recorder.frames:
            try:
                audio_data = b''.join(self.recorder.frames[-10:])
                arr = np.frombuffer(audio_data, dtype=np.int16)
                if len(arr) > 0:
                    self.line.set_data(np.arange(len(arr)), arr)
                    self.ax.set_xlim(0, len(arr))
                    self.canvas.draw()
            except:
                pass
    
    def get_audio_array(self):
        if self.recorder.frames and len(self.recorder.frames) > 0:
            try:
                audio_data = b''.join(self.recorder.frames)
                return np.frombuffer(audio_data, dtype=np.int16)
            except:
                return None
        return None
    
    def mostrar_tabla_entropia_audio(self):
        try:
            audio_array = self.get_audio_array()
            if audio_array is None or len(audio_array) == 0:
                QMessageBox.warning(self, "Advertencia", "No hay audio grabado")
                return
            
            entropia, tabla, N = calcular_entropia_con_tabla(audio_array)
            duracion = N / 44100
            
            self.ventana_audio = QTextEdit()
            self.ventana_audio.setWindowTitle("📊 Tabla de Entropía - Audio")
            self.ventana_audio.setReadOnly(True)
            self.ventana_audio.setFontFamily("Courier New")
            self.ventana_audio.setFontPointSize(9)
            self.ventana_audio.setText(f"""
=== TABLA DE ENTROPÍA DE SHANNON - AUDIO ===
Entropía total: {entropia:.4f} bits
Total de muestras: {N}
Duración: {duracion:.2f} segundos
Frecuencia de muestreo: 44100 Hz

{tabla}
""")
            self.ventana_audio.resize(1000, 700)
            self.ventana_audio.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al calcular entropía: {str(e)}")

# ----------------- Extractor de Matriz de imagenes -----------------
class MatrixExtractorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.max_res = (256, 256)
        self.original_image_path = None
        self.current_numpy_matrix = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel(f"🔢 Extractor de Matriz de Píxeles ({self.max_res[0]}x{self.max_res[1]})")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        controls_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("📷 Cargar Imagen")
        self.load_btn.clicked.connect(self.load_image_path)
        controls_layout.addWidget(self.load_btn)

        mode_group = QGroupBox("Modo de Extracción")
        mode_layout = QHBoxLayout()
        self.rgb_radio = QRadioButton("RGB")
        self.gray_radio = QRadioButton("Escala de Grises")
        self.rgb_radio.setChecked(True)
        mode_layout.addWidget(self.rgb_radio)
        mode_layout.addWidget(self.gray_radio)
        mode_group.setLayout(mode_layout)
        controls_layout.addWidget(mode_group)

        self.process_btn = QPushButton("💾 Procesar y Guardar Matriz")
        self.process_btn.clicked.connect(self.process_and_save_matrix)
        controls_layout.addWidget(self.process_btn)
        
        self.entropy_btn = QPushButton("📊 Mostrar Tabla de Entropía (256 niveles)")
        self.entropy_btn.clicked.connect(self.mostrar_tabla_entropia_imagen)
        controls_layout.addWidget(self.entropy_btn)
        
        layout.addLayout(controls_layout)
        
        result_layout = QHBoxLayout()

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(self.max_res[0], self.max_res[1])
        self.image_label.setStyleSheet("border: 2px dashed #3498db; border-radius: 5px; background-color: #ecf0f1;")
        self.image_label.setText("Imagen aparecerá aquí\n(Redimensionada a 256x256)")
        result_layout.addWidget(self.image_label)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setPlaceholderText("Información de la matriz y fragmento de píxeles aparecerán aquí...")
        result_layout.addWidget(self.info_text)
        
        layout.addLayout(result_layout)
        self.setLayout(layout)

    def load_image_path(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen", "", 
            "Archivos de imagen (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            self.original_image_path = file_path
            self.info_text.setText(f"Archivo seleccionado: {os.path.basename(file_path)}\nListo para procesar.")
            self.display_preview(file_path)
        else:
            self.original_image_path = None
    
    def display_preview(self, file_path):
        try:
            img = Image.open(file_path)
            img_preview = img.resize(self.max_res, Image.LANCZOS).convert('RGB')
            data = img_preview.tobytes("raw", "RGB")
            qimage = QImage(data, img_preview.width, img_preview.height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            self.image_label.setPixmap(pixmap)
        except Exception as e:
            self.image_label.setText(f"Error al mostrar preview: {e}")
            self.image_label.clear()
            QMessageBox.critical(self, "Error", f"No se pudo cargar la imagen: {e}")

    def process_and_save_matrix(self):
        if not self.original_image_path:
            QMessageBox.warning(self, "Advertencia", "Primero debes cargar un archivo de imagen.")
            return

        mode = 'RGB' if self.rgb_radio.isChecked() else 'L'
        
        try:
            img = Image.open(self.original_image_path)
            img_processed = img.resize(self.max_res, Image.LANCZOS).convert(mode)
            matriz = np.array(img_processed)
            
            self.current_numpy_matrix = matriz.copy()
            
            file_base = os.path.basename(self.original_image_path).split('.')[0]
            file_name = f"matriz_datos_{mode}_{file_base}.txt"
            
            if matriz.ndim > 2:
                datos_a_guardar = matriz.reshape(-1, 3)
            else:
                datos_a_guardar = matriz.reshape(-1, 1)

            np.savetxt(file_name, datos_a_guardar, fmt='%d', 
                      header=f'Matriz de Pixeles {mode} de {self.max_res[0]}x{self.max_res[1]}')
            
            self.info_text.setText("--- PROCESAMIENTO EXITOSO ---\n\n")
            self.info_text.append(f"Modo de Matriz: **{mode}**\n")
            self.info_text.append(f"*La matriz COMPLETA se guardó en: {file_name}*\n")
            self.info_text.append(f"*Matriz guardada en memoria para cálculo de entropía*\n\n")
            self.info_text.append("--- Fragmento de la Matriz (Primeros 5x5 Píxeles) ---\n")
            
            if mode == 'RGB':
                self.info_text.append(f"[R, G, B]:\n{matriz[:5, :5].tolist()}\n")
            else:
                self.info_text.append(f"[Intensidad]:\n{matriz[:5, :5].tolist()}\n")

            QMessageBox.information(self, "Proceso Completo", 
                                   f"Matriz guardada en:\n{file_name}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al procesar imagen: {str(e)}")
    
    def mostrar_tabla_entropia_imagen(self):
        try:
            if self.current_numpy_matrix is None:
                QMessageBox.warning(self, "Advertencia", 
                                   "Primero procesa una imagen con 'Procesar y Guardar Matriz'")
                return
            
            if self.current_numpy_matrix.ndim == 3:
                matriz_gris = np.dot(self.current_numpy_matrix[...,:3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)
                modo = "RGB convertido a grises"
            else:
                matriz_gris = self.current_numpy_matrix
                modo = "Escala de grises"
            
            entropia, tabla, N = calcular_entropia_con_tabla(matriz_gris)
            
            self.ventana_imagen = QTextEdit()
            self.ventana_imagen.setWindowTitle("📊 Tabla de Entropía - Imagen (256 niveles)")
            self.ventana_imagen.setReadOnly(True)
            self.ventana_imagen.setFontFamily("Courier New")
            self.ventana_imagen.setFontPointSize(8)
            self.ventana_imagen.setText(f"""
=== TABLA DE ENTROPÍA DE SHANNON - IMAGEN ===
Archivo: {os.path.basename(self.original_image_path) if self.original_image_path else 'Desconocido'}
Modo: {modo}
Dimensiones: {self.max_res[0]} x {self.max_res[1]} píxeles
Total de píxeles: {N}
Entropía total: {entropia:.4f} bits

{tabla}
""")
            self.ventana_imagen.resize(1100, 750)
            self.ventana_imagen.show()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al calcular entropía: {str(e)}")

# ----------------- Ventana Principal -----------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analizador Texto Audio e Imagenes")
        self.setGeometry(100,100,1000,800)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        self.show_welcome_screen()
    
    def show_welcome_screen(self):
        for i in reversed(range(self.main_layout.count())):
            self.main_layout.itemAt(i).widget().setParent(None)
        self.welcome = WelcomeScreen(self)
        self.main_layout.addWidget(self.welcome)
    
    def show_main_interface(self):
        for i in reversed(range(self.main_layout.count())):
            self.main_layout.itemAt(i).widget().setParent(None)
        layout = QHBoxLayout()
        nav = QVBoxLayout()
        text_btn = QPushButton("📝 Texto")
        voice_btn = QPushButton("🎤 Voz")
        image_btn = QPushButton("🎨 Imagen")
        nav.addWidget(text_btn)
        nav.addWidget(voice_btn)
        nav.addWidget(image_btn)
        nav.addStretch()
        layout.addLayout(nav)
        
        self.stacked = QStackedWidget()
        self.text_widget = TextAnalyzerWidget()
        self.voice_widget = VoiceRecorderWidget()
        self.image_widget = MatrixExtractorWidget()
        self.stacked.addWidget(self.text_widget)
        self.stacked.addWidget(self.voice_widget)
        self.stacked.addWidget(self.image_widget)
        layout.addWidget(self.stacked)
        self.main_layout.addLayout(layout)
        
        text_btn.clicked.connect(lambda:self.stacked.setCurrentIndex(0))
        voice_btn.clicked.connect(lambda:self.stacked.setCurrentIndex(1))
        image_btn.clicked.connect(lambda:self.stacked.setCurrentIndex(2))

# ----------------- Main -----------------
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()