# Reporte de Análisis: Modificación de Centroides y Dispersión en K-Means

## Configuración de Parámetros

| Parámetro | Original | Modificada |
| --- | --- | --- |
| **Centroides (blob_centers)** | `[[ 0.2,  2.3],[-1.5 ,  2.3],[-2.8,  1.8], [-2.8,  2.8], [-2.8,  1.3]]` | `[[ 0.2,  2.3], [-1.5 ,  2.3], [-2.8,  1.8], [-2.8, 2.8], [-2.8,  1]]` |
| **Desviación Estándar (blob_std)** | `[0.4, 0.3, 0.1, 0.1, 0.1]` | `[0.3, 0.2, 0.08, 0.08, 0.08]` |

---

## Comparación y Análisis de Resultados

### A. Distribución Espacial (Scatter Plot / blobs_plot)
**Configuración Original:** Los tres blobs ubicados en la coordenada $x_1 = -2.8$ presentaban un solapamiento considerable y se encontraban aglomerados en el eje vertical, lo que impedía que el algoritmo K-Means distinguiera con claridad los límites de cada grupo. Eso provocaba que se considere como un grupo y al estar definido con 5 cluster el grupo con mayor dispersión se dividiera en 2 secciones.

<figure>
    <img src="imagenes/blobs_plot_1.png"  width="300">
</figure>

**Configuración Modificada:** Al desplazar el último centroide de $1.3$ a $1.0$ y reducir la desviación estándar, se logra una separación vertical limpia y bien definida. Las tres nubes de la izquierda quedan perfectamente aisladas en el eje $x_2$ (alrededor de 1.0, 1.8 y 2.8). Esto permitiendo al algortirmo K-means pueda seperar en 5 grupos perfectamente los datos.

<figure>
    <img src="imagenes/blobs_plot_2.png"  width="300">
</figure>


### B. Método del Codo y Curva de Inercia
* **Configuración Original:** Debido al amontonamiento de los datos, la gráfica de inercia presentaba ambigüedades y solía sugerir erróneamente un número óptimo menor (como $k = 4$) esto porque despues de 4 cluster la mejora ya no era relevante y se consideraba minima.

El algoritmo K-Means busca minimizar la inercia (la distancia cuadrática media de los puntos a su centroide más cercano) y los tres blobs de la izquierda comparten exactamente la misma coordenada $x$ ($-2.8$) y están muy cerca unos de otros.

<figure>
    <img src="imagenes/inertia_vs_k_plot_1.png"  width="300">
</figure>

**Configuración Modificada:** Al eliminar el solapamiento y compactar los clústeres, la inercia desciende de manera más precisa y el punto de inflexión (*elbow*) se alinea correctamente con el número real de grupos latentes ($k = 5$). En este caso el codo se marca como 4, sin embargo cuando lo complementamos con el diagrama de silueta a pesar que menciona que usar un número de clusters superiores a 4 ya no es relevante en este caso si es recomendable usar 5 cluster que separan los grupos.

Esto sucede porque el método del codo busca el punto donde la reducción de la inercia empieza a desacelerarse de forma drástica. Sin embargo, matemáticamente la inercia siempre baja conforme aumentas $k$ no debemos confiar solamente en una métrica para saber el correcto numero de cluster optimos para los datos.

<figure>
    <img src="imagenes/inertia_vs_k_plot_2.png"  width="300">
</figure>

### C. Diagrama de Silueta
**Configuración Original:** Los puntajes de silueta para $k = 5$ mostraban barras irregulares y anchuras desequilibradas causadas por la mala clasificación de puntos en las zonas de traslape.

<div style="display: flex; gap: 10px;">
    <figure>
        <img src="imagenes/silhouette_score_vs_k_plot_1.png"  width="300">
    </figure>
    <figure>
        <img src="imagenes/silhouette_analysis_plot_1.png"  width="200">
    </figure>
</div>

**Configuración Modificada:** Con la nueva separación y menor dispersión, los diagramas de silueta muestran formas más homogéneas, simétricas y anchas que superan el límite de la línea roja del promedio global, confirmando una alta cohesión interna y una separación óptima.

<div style="display: flex; gap: 10px;">
    <figure>
        <img src="imagenes/silhouette_score_vs_k_plot_2.png"  width="300">
    </figure>
    <figure>
        <img src="imagenes/silhouette_analysis_plot_2.png"  width="200">
    </figure>
</div>

---

## 3. Conclusión

Modificar las coordenadas de los centroides y reducir la desviación estándar resolvió los problemas estructurales del conjunto de datos. Al otorgar mayor independencia espacial a los blobs de la izquierda y por lo tanto lograr seperar los datos, por lo tanto aunque el método del codo como el análisis de silueta no reflejan de forma fidedigna que el valor óptimo de clústeres **$k = 5$**, se puede intentar mejorar disminuyendo la dispercion de los datos. En este caso funcionó para seperar los datos con **$k = 5$** clusters.

<div style="display: flex; gap: 10px;">
    <figure>
        <img src="imagenes/voronoid_plot_1.png"  width="300">
        <figcaption>Gráfica de Voronoid original</figcaption>
    </figure>
    <figure>
        <img src="imagenes/voronoid_plot_2.png"  width="300">
        <figcaption>Gráfica de Voronoid actualizada</figcaption>
    </figure>
</div>


### Reto opcional 

Para el caso de incrementar la desviación estándar de los valores .01 a .4 los datos se dispersarían a pesar de usar los centroides ópticos encontrados por Géron los datos dispersados perjudicarían la forma de dividir los datos en los 5 clusters definidos.

```python
blob_centers = np.array(
    [[ 0.2,  2.3],
     [-1.5 ,  2.3],
     [-2.8,  2],
     [-2.8,  3],
     [-2.8,  1]])
blob_std = np.array([0.4, 0.3, 0.4, 0.4, 0.4])
```

<figure>
    <img src="imagenes/blobs_plot_3.png"  width="300">
</figure>

A simple vista solo se pueden detectar 3 grupos de datos, aunque la gráfica de inercia nos marca que existen al menos 4 clusters necesarios para dividir los datos.

<figure>
    <img src="imagenes/inertia_vs_k_plot_3.png"  width="300">
</figure>


<figure>
    <img src="imagenes/voronoid_plot_3.png"  width="300">
    <figcaption>Gráfica de Voronoid actualizada</figcaption>
</figure>