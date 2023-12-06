
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly as plt
import plotly.graph_objects as go
import exchange_calendars as xcals
from datetime import date
import geopandas as gpd
import matplotlib.pyplot as plt


def download_data(tickers, start_date='2001-01-01', end_date=date.today().strftime('%Y-%m-%d')):
    data = yf.download(tickers, start=start_date, end=end_date)

    return data['Close']

def calcular_fechas(hoy: pd.Timestamp):
    # Obtén el calendario de la bolsa de México
    xmex = xcals.get_calendar("XMEX")

    # Si el día de la semana es lunes (0 en el sistema Python weekday()), retrocede 3 días
    if hoy.weekday() == 0:
        prev_business_day = hoy - pd.Timedelta(days=3)
    # De lo contrario, solo retrocede un día
    else:
        prev_business_day = hoy - pd.Timedelta(days=1)

    # Si el día calculado no es un día hábil, busca el día hábil más reciente
    if not xmex.is_session(prev_business_day):
        prev_business_day = xmex.previous_close(prev_business_day).to_pydatetime()

    ayer = prev_business_day

    # Crear un diccionario para almacenar los resultados
    resultado = {}

    # Mes hasta la fecha
    primer_dia_mes = xmex.date_to_session(hoy.replace(day=1), direction="next")
    if hoy == primer_dia_mes:
        # Si hoy es el primer día hábil del mes, toma el primer día hábil del mes anterior
        mes_anterior = hoy - pd.DateOffset(months=1)
        primer_dia_mes = xmex.date_to_session(mes_anterior.replace(day=1), direction="next")

    # Calcula los días hábiles entre el primer día del mes y hoy
    dias_habiles = len(xmex.sessions_in_range(primer_dia_mes, hoy))+1

    # Usa estos días hábiles para obtener la ventana de sesiones
    mes_hasta_fecha = xmex.sessions_window(hoy, -dias_habiles)

    # Año hasta la fecha
    primer_dia_año = xmex.date_to_session(hoy.replace(month=1, day=1), direction="next")
    if hoy == primer_dia_año:
        # Si hoy es el primer día hábil del año, toma el primer día hábil del año anterior
        año_anterior = hoy - pd.DateOffset(years=1)
        primer_dia_año = xmex.date_to_session(año_anterior.replace(month=1, day=1), direction="next")

    # Calcula los días hábiles entre el primer día del año y hoy
    dias_habiles = len(xmex.sessions_in_range(primer_dia_año, hoy))+1

    # Usa estos días hábiles para obtener la ventana de sesiones
    año_hasta_fecha = xmex.sessions_window(hoy, -dias_habiles)

    # Fecha de hace un mes
    hace_un_mes = hoy - pd.DateOffset(months=1)

    # Encuentra el día hábil más cercano en el pasado a hace_un_mes
    dia_habil_hace_un_mes = xmex.date_to_session(hace_un_mes, direction="previous")

    # Obtén todas las sesiones desde hace_un_mes hasta hoy
    ultimos_30_dias = xmex.sessions_in_range(dia_habil_hace_un_mes, hoy)

    # Fecha de hace tres meses
    hace_tres_meses = hoy - pd.DateOffset(months=3)

    # Encuentra el día hábil más cercano en el pasado a hace_tres_meses
    dia_habil_hace_tres_meses = xmex.date_to_session(hace_tres_meses, direction="previous")

    # Obtén todas las sesiones desde hace_tres_meses hasta hoy
    ultimos_90_dias = xmex.sessions_in_range(dia_habil_hace_tres_meses, hoy)

    # Fecha de hace seis meses
    hace_seis_meses = hoy - pd.DateOffset(months=6)

    # Encuentra el día hábil más cercano en el pasado a hace_seis_meses
    dia_habil_hace_seis_meses = xmex.date_to_session(hace_seis_meses, direction="previous")

    # Obtén todas las sesiones desde hace_seis_meses hasta hoy
    ultimos_180_dias = xmex.sessions_in_range(dia_habil_hace_seis_meses, hoy)

    # Fecha de hace un año
    hace_un_año = hoy - pd.DateOffset(years=1)

    # Encuentra el día hábil más cercano en el pasado a hace_un_año
    dia_habil_hace_un_año = xmex.date_to_session(hace_un_año, direction="previous")

    # Obtén todas las sesiones desde hace_un_año hasta hoy
    ultimos_365_dias = xmex.sessions_in_range(dia_habil_hace_un_año, hoy)

    resultado['mes_hasta_fecha'] = mes_hasta_fecha
    resultado['año_hasta_fecha'] = año_hasta_fecha
    resultado['ultimos_30_dias'] = ultimos_30_dias
    resultado['ultimos_90_dias'] = ultimos_90_dias
    resultado['ultimos_180_dias'] = ultimos_180_dias
    resultado['ultimos_365_dias'] = ultimos_365_dias

    return resultado

def anualizar_rendimiento(rendimiento_bruto, dias):
    rendimiento_anualizado = rendimiento_bruto / dias * 360
    return rendimiento_anualizado

def calcular_rendimiento_bruto(precio_inicio, precio_fin, dias):
    # Calcular el cambio porcentual en el precio
    cambio_pct = (precio_fin / precio_inicio) - 1

    # Calcular el rendimiento bruto
    rendimiento_bruto = cambio_pct
    return rendimiento_bruto

def calcular_rendimiento(precios, ventanas_de_tiempo, nombre_benchmark):
    rendimientos = []

    for periodo, ventana in ventanas_de_tiempo.items():
        # Obtén los precios de inicio y fin para la ventana de tiempo actual
        precio_inicio = precios.loc[ventana[0], nombre_benchmark]
        precio_fin = precios.loc[ventana[-1], nombre_benchmark]

        # Calcula el rendimiento bruto y anualizado
        rendimiento_bruto = calcular_rendimiento_bruto(precio_inicio, precio_fin, (ventana[-1] - ventana[0]).days)
        rendimiento_anualizado = anualizar_rendimiento(rendimiento_bruto, (ventana[-1] - ventana[0]).days)

        # Agrega el rendimiento a la lista de rendimientos
        rendimientos.append({
            'Periodo': periodo,
            'Rendimiento_bruto': rendimiento_bruto*100,
            'Rendimiento_anualizado': rendimiento_anualizado*100
        })

    # Convierte la lista de rendimientos en un dataframe
    df_rendimientos = pd.DataFrame(rendimientos)

    return df_rendimientos


# Descarga de la información de los activo
tickers = ['IEMB.MI', 'EWZ', 'STIP', "IVV", "IAU"]

activos=download_data(tickers)
activos = activos.dropna()

df_activos = activos.copy()


# Opciones de navegación
st.sidebar.title("Navegación")
option = st.sidebar.radio("Seleccione una página", ["Activos", "Portafolios"])

#
#
#
#

# Precios de los activos
if option == "Activos":
    st.title("Resumen y Estadisticas del activo")
    activo = st.sidebar.selectbox(
        "Elige un activo",
        ('IEMB.MI', 'EWZ', "STIP", "IVV", "IAU")
    )
    df_activo = df_activos[activo]

    st.header("Precios")
    # Crear la figura
    fig = go.Figure()

    # Agregar los datos del activo a la figura
    fig.add_trace(go.Scatter(x=df_activo.index, y=df_activo.values, mode='lines'))

    # Establecer títulos y etiquetas
    fig.update_layout(title='Precio de cierre historico del activo',
                    xaxis_title='Fecha',
                    yaxis_title='Precio de Cierre (en $)')

    st.plotly_chart(fig)

    # Rendimientos
    st.header("Rendimientos")
    st.markdown("Elige la fecha a la que quieres los rendimientos cuidando que no sea un fin de semana o el día actual:")

    hoy = st.date_input('Introduce la fecha')
    hoy = pd.Timestamp(hoy)
    ventanas_de_tiempo = calcular_fechas(hoy)

    df_rendimientos = calcular_rendimiento(activos, ventanas_de_tiempo, activo)

    st.dataframe(df_rendimientos)


# Información por activo

if option == "Activos":
    if activo == "IEMB.MI":
        st.header("Información general")
        st.markdown("El ETF **IEMB** pretende replicar la rentabilidad de un índice compuesto por bonos denominados en dólares estadounidenses de países emergentes, por lo que al tenerlo en nuestro portafolio, nos encontraremos expuestos a diversos bonos guberamentales y cuasi-gubernamentales de mercados emergentes emitidos en dólares, los cuales tienen un grado de grado de inversión y de alto rendimiento.")
        st.markdown("El fondo se constituyo el 15 de Febrero del 2008 y cuenta con 57,372,365 activos de circulación al 01 de Diciembre del 2023")
        st.markdown("Su índice de referencia es JPMorgan EMBI Global Core Index (JPEICORE), el cual esta compuesto por bonos gubernamentales denominados en dólares estadounidenses emitidos por países de mercados emergentes, contando con una beta de 1.00 al 30/Nov/2023, indicando que nuestro ETF y su indice registran un mismo comportamiento.")

        st.header("Posiciones principales")
        st.write("Nuestro ETF tiene un total de 615 posiciones, todas con Renta Fija como Clase de activo, de entre las cuales 10 principales son las siguientes;")
        emisor = ["TURKEY (REPUBLIC OF)","SAUDI ARABIA (KINGDOM OF)","BRAZIL FEDERATIVE REPUBLIC OF (GOVERNMENT)",
         "PHILIPPINES (REPUBLIC OF)", "COLOMBIA (REPUBLIC OF)", "DOMINICAN REPUBLIC (GOVERNMENT)", "MEXICO (UNITED MEXICAN STATES) (GOVERNMENT)",
          "QATAR (STATE OF)", "INDONESIA (REPUBLIC OF)", "OMAN SULTANATE OF (GOVERNMENT)"	]
        peso = [4.48, 3.93, 3.80, 3.54, 3.41, 3.39, 3.27, 3.25, 3.04, 2.97]
        Tabla_posiciones = pd.DataFrame(list(zip(emisor, peso)), columns=['Emisor', 'Peso (%)'])
        st.write(Tabla_posiciones)

        st.header(" Exposición")
        exposicion = st.selectbox('Selecciona el tipo de exposición', ['Geográfica', 'Vencimiento', 'Cálidad crediticia'])

        if exposicion == 'Geográfica':
            st.subheader("Geográfica")
            st.markdown("Dentro de este ETF se puede apreciar una gran diversificación de los paises a los que tiene exposición, dado que si bien hay algunos con un poco mas de porcentaje, no hay mucha diferencia entre sí, entro los porcentajes más altos, encontramos a México, Arabia Saudita, Turquía e Indonesia, con un porcentaje mayor al 5% cada una como se muestra a continuación.")

            world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
            paises_destacados = {"Mexico": 5.91,"Saudi Arabia": 5.73,"Turkey": 5.24,"Indonesia": 5.19,"United Arab Emirates": 4.60,"Qatar": 4.11,"China": 3.81,"Brazil": 3.80,
                                 "Oman": 3.64,"Philippines": 3.61,"Colombia": 3.41,"Dominican Republic": 3.39,"Chile": 3.35,"South Africa": 3.13,"Peru": 2.94,"Panama": 2.89,"Bahrain": 2.75,"Hungary": 2.59,
                                 "Egypt": 2.46,"Uruguay": 2.22,"Romania": 2.17,"Poland": 2.04,"Malaysia": 2.03,"Nigeria": 2.01,"Argentina": 1.80,"Angola": 1.15,"Costa Rica": 1.10,"Liquidity": 0.21,"Other": 12.70}
            world['Destacado'] = world['name'].map(lambda x: paises_destacados.get(x, 0))
            fig, ax = plt.subplots(1, 1, figsize=(15, 10))
            world.boundary.plot(ax=ax, linewidth=1)
            world.plot(column='Destacado', cmap='OrRd', ax=ax, legend=True, legend_kwds={'label': "Porcentaje destacado (%)", 'orientation': "horizontal"})
            #st.pyplot(fig)

            paises = ["México", "Arabia Saudita", "Turquía", "Indonesia", "Emiratos Árabes Unidos", "Qatar", "China", "Brasil", "Omán", "Filipinas", "Colombia", "República Dominicana",
            "Chile", "Sudáfrica", "Perú", "Panamá", "Baréin", "Hungría", "Egipto", "Uruguay", "Rumania", "Polonia", "Malasia", "Nigeria", "Argentina", "Angola", "Costa Rica", "Liquidez", "Otros"]
            porcentaje = [5.91, 5.73, 5.24, 5.19, 4.60, 4.11, 3.81, 3.80, 3.64, 3.61, 3.41, 3.39, 3.35, 3.13, 2.94, 2.89, 2.75, 2.59, 2.46, 2.22, 2.17, 2.04, 2.03, 2.01, 1.80, 1.15, 1.10, 0.21, 12.70]
            Tabla_paises = pd.DataFrame(list(zip(paises, porcentaje)), columns=['Pais', 'Porcentaje'])
            #st.write(Tabla_paises)
    
            col1, col2 = st.columns([2, 4])
            col1.write(Tabla_paises)
            col2.pyplot(fig)

        elif exposicion == 'Vencimiento':
            st.subheader("Vencimiento")
            st.markdown("En su mayoría vemos una alta exposición a bonos de largo plazo con poco mas de una cuarta parte de dicho portafolio invertido en un plazo a más de 20 años indicando muy poca liquidez")
            vencimiento = ['Efectivo y derivados', '0 a 1 año', '1 a 2 años', '2 a 3 años', '3 a 5 años', '5 a 7 años', '7 a 10 años', '10 a 15 años', '15 a 20 años', 'Más de 20 años']
            porcentajes = [0.25, 2.15, 6.03, 6.93, 16.17, 13.00, 18.13, 6.66, 4.26, 26.44]
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(vencimiento, porcentajes, color='cornflowerblue')
            ax.set_xlabel('Porcentaje (%)')
            ax.set_title('Distribución de Activos por Plazo de Inversión')
            st.pyplot(fig)

        elif exposicion == 'Cálidad crediticia':
            st.subheader('Cálidad crediticia')
            st.markdown("La cálidad crediticia de un poco más de la mitad de este portafolio tiene una calificación entre AA, A y BBB, se debe tener cuidado puesto que la otra parte del portafolio se encuentra por debajo del grado de inversión, entrando en un grado especulativo ")
            categorias = ['Liquidez', 'Calificación AA', 'Calificación A', 'Calificación BBB', 'Calificación BB', 'Calificación B', 'Calificación CCC', 'Calificación CC', 'Calificación C', 'Calificación D', 'Sin calificación']
            porcentajes_calificaciones = [0.25, 7.52, 16.62, 27.99, 21.49, 19.08, 2.42, 2.53, 0.00, 1.76, 0.35]
            # Crear el gráfico de barras
            fig, ax = plt.subplots(figsize=(10, 6))
            k = ax.bar(categorias, porcentajes_calificaciones, color='cornflowerblue')
            ax.set_xlabel('Categoría')
            ax.set_ylabel('Porcentaje (%)')
            ax.set_title('Distribución de Activos por Calificación')
            ax.tick_params(axis='x', rotation=45) 
            for i in k:
                yval = i.get_height()
                plt.text(i.get_x() + i.get_width()/2, yval + 0.5, f'{yval:.1f}%', ha='center', va='bottom', fontsize=8, color='black')
            st.pyplot(fig)


    elif activo == "EWZ":
        st.header("Información general")
        st.markdown("El ETF **EWZ** replica los resultados de inversión de un índice compuesto por valores de renta variable de Brasil, dando exposición a grandes y medianas empresas con un acceso del  85 % del mercado de acciones brasileñas. El fondo fue constituido el 10 de Julio del 2000, con USD como su divisa base")
        st.markdown("Su índice de referencia es MSCI Brazil 25/50 Index(M1BR2550), cuenta con una beta de 0.99 indicando que el ETF tiende a ser ligeramente menos volátil que el mercado dado su índice de referencia")
       
        st.header("Posiciones principales")
        st.markdown("Observacion. En su mayoria las clases de activos son equity")
        data = {
          'Ticker': ['VALE3', 'PETR4', 'ITUB4', 'PETR3', 'BBDC4', 'B3SA3', 'ABEV3', 'WEGE3', 'RENT3', 'BBAS3'],
          'Nombre': ['CIA VALE DO RIO DOCE SH', 'PETROLEO BRASILEIRO PREF SA', 'ITAU UNIBANCO HOLDING PREF SA', 'PETROLEO BRASILEIRO SA PETROBRAS', 'BANCO BRADESCO PREF SA', 'B3 BRASIL BOLSA BALCAO SA', 'AMBEV SA', 'WEG SA', 'LOCALIZA RENT A CAR SA', 'BANCO DO BRASIL SA'],
          'Sector': ['Materiales', 'Energía', 'Financieros', 'Energía', 'Financieros', 'Financieros', 'Productos básicos de consumo', 'Industriales', 'Industriales', 'Financieros'],
          'Clase de activos': ['Equity']*10,
          'Peso (%)': [12.75, 8.37, 7.69, 6.82, 4.22, 3.95, 3.27, 3.14, 3.0, 2.59]         } 
        dfposiciones = pd.DataFrame(data)
        st.write(dfposiciones)

        st.header("Exposición")  
        st.markdown("Se puede observar un portafolio diversificado sectorialmente, tenemos alrededor de un 25% de nuestro portafolio invertido en acciones financieras, aproximadamente 40% en el sector de energía y materiales,  al rededor de 25% entre servicios, industriales y básicos de consumo y el demás porcentaje dividido en otros sectores.")
        sectores = ['Financieros', 'Energía', 'Materiales', 'Servicios', 'Industriales','Productos básicos de consumo', 'Cuidado de la Salud', 'Consumo discrecional','Comunicación', 'Efectivo y Derivados', 'Tecnología de la Información']
        porcentajes = [25.89, 19.14, 17.92, 9.75, 8.84, 8.05, 2.55, 2.44, 2.41, 2.24, 0.76]
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(sectores,porcentajes, color='cornflowerblue')
        ax.set_title('Distribución de Sectores en (%)')
        st.pyplot(fig)


    elif activo == "STIP":
        st.header("Información general")
        st.markdown("EL ETF **STIP** busca replicar el índice ICE US Treasury 0-5 Year Inflation Linked Bond Index (USD) (CETIPO), el cual se encuentra compuesto por bonos del Tesoro de EE.UU. protegidos contra la inflación y amortizaciones menores a 5 años, el ETF cuenta con una beta de 0.12 lo que nos indica que es mucho menos volatil y por ende menos riesgoso que el indice que esta replicando")
        st.markdown("Fue creado el 01 de Diciembre del 2010 y tiene USD como divisa base. Este se encuentra expuesto a U.S. TIPS, bonos del gobierno cuyo valor nominal aumenta con la inflación, teniendo un acceso dirigido a una sección especifica del mercado doméstico de TIPS")

        st.header("Exposición")
        st.markdown("Dada la composición que tiene, encontramos que su mayor emisor es UNITED STATES TREASURY en un 99.99%, por lo  mismo se encuentra enfocada su inversion en Bonos del Tesoro en un 99.99% y el 0.01% restante se encuentra en derivados y liquidez, por ende su cálidad crediticia es de alto grado, pues la calificación corresponde a un AA.")
        st.markdown("Encontramos entonces que este ETF no tiene mucha diversificación a excepción del vencimiento de sus bonos que va desde los 0-5 años dado el índice que busca replicar, teniendo aproximadamente un 40% de su portafolio en bonos a vencer en 3-5 años y un 20% a un año por lo que no posee un alto riesgo de liquidez.")
        
        vencimiento = ['0 a 1 año', '1 a 2 años', '2 a 3 años', '3 a 5 años']
        porcentajes = [19.91, 22.05, 16.77, 41.27]
        fig, ax = plt.subplots()
        ax.pie(porcentajes, labels=vencimiento, autopct='%1.1f%%', startangle=90, colors=['skyblue', 'royalblue', 'steelblue', 'cornflowerblue'])
        ax.axis('equal')  # Equal aspect ratio asegura que el pastel sea circular.
        plt.title("Vencimiento de los bonos")
        st.pyplot(fig)


    elif activo == "IVV":
        st.header("Información general")
        st.markdown("El ETF **IVV**, replica al conocido índice S&P 500 (SPTR) compuesto de renta variable de alta capitalización de EE.UU, de ese modo este ETF tiene exposición a 500 grandes empresas establecidas en EE.UU, ofreciendo además un bajo costo por dicha exposición. Su respectiva Beta es de 1.00 por lo que hay un mismo comportamiento entre el ETF y el índice")
        
        st.header("Posiciones principales")
        st.markdown("Podemos observar que en sus principales posiciones tenemos empresas tipo growth, ya que principalmente sus acciones pertenecen al sector de tecnología.")
        st.markdown("Observación. En su mayoría las clases de activos son equity")
        data = {'Ticker': ['AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'GOOG', 'TSLA', 'BRKB', 'UNH'],
                'Nombre': ['APPLE INC', 'MICROSOFT CORP', 'AMAZON COM INC', 'NVIDIA CORP', 'ALPHABET INC CLASS A', 'META PLATFORMS INC CLASS A', 'ALPHABET INC CLASS C', 'TESLA INC', 'BERKSHIRE HATHAWAY INC CLASS B', 'UNITEDHEALTH GROUP INC'],
                 'Sector': ['Tecnología de la Información', 'Tecnología de la Información', 'Consumo discrecional', 'Tecnología de la Información', 'Comunicación', 'Comunicación', 'Comunicación', 'Consumo discrecional', 'Financieros', 'Cuidado de la Salud'],
                 'Clase de activo': ['Equity'] * 10,
                 'Peso (%)': [7.24, 7.13, 3.42, 2.92, 1.99, 1.85, 1.71, 1.69, 1.69, 1.32] }
        tabla_posicion = pd.DataFrame(data) 
        st.table(tabla_posicion)

        st.header("Exposición")
        st.markdown("Hay una exposición sectorial muy diversificada, donde el mayor peso del portafolio cae en acciones del sector tecnología de la información en aproximadamente un 30%.")
        sector = ['Tecnología de la Información', 'Financieros', 'Cuidado de la Salud', 'Consumo discrecional', 'Comunicación', 'Industriales', 'Productos básicos de consumo', 'Energía', 'Inmobiliario', 'Materiales', 'Servicios', 'Efectivo y Derivados']
        porcentajes = [28.63, 13.00, 12.71, 10.77, 8.44, 8.40, 6.31, 4.09, 2.49, 2.43, 2.41, 0.32]
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(sector, porcentajes, color='cornflowerblue')
        ax.set_xlabel('(%)')
        ax.set_title('Distribución Sectorial')
        st.pyplot(fig)

    elif activo == "IAU":
        st.header("Información general")
        st.markdown("El ETF **IAU** busca replicar al LBMA Gold Price (LBMA Gold Price). Este ETF tiene una beta de 0.08, por lo que su volatilidad y su riesgo con el mercado en comparación al índice es un poco menor.")
        st.markdown("Este ETF dado el índice que busca replicar da una exposición a los movimientos diarios del lingote de oro, dando un cómodo acceso al precio del lingote de oro. Además se encuentra respaldado por oro físico, contando con 396,10 toneladas en custodia al 05 de Diciembre del 2023")
        st.markdown("Fue constituido el 25 de Enero del 2005, tiene a USD como divisa base y su clase de activo dada su composición es materias primas")
