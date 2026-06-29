# NOTES
# Just need to create website link/host so anyone can run without python code

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import interp1d
from scipy.optimize import root_scalar
import io
from pathlib import Path


##### Title Header ####
st.set_page_config(page_title="Gel Point Calculator",
                   page_icon="🧪",
                   layout="wide")

st.title("🧪 Gel Point Calculator")


#### File Upload ####
uploaded_file = st.file_uploader(
    "Upload a TRIOS Excel file",
    type=["xls","xlsx"]
)



if uploaded_file is not None:
    base_name = Path(uploaded_file.name).stem
    file_id = (uploaded_file.name, uploaded_file.size)
    if "file_id" not in st.session_state:
        st.session_state.file_id = file_id

    if file_id != st.session_state.file_id:

        # Clearing data if new file is uploaded
        for key in [
            "gel_point",
            "y_gel_point",
            "gel_point_dosage"
        ]:
            st.session_state.pop(key, None)

        st.session_state.file_id = file_id

    rxn_start = st.number_input(
        "Rxn Start - Time Delay (s)",
        value = 10
    )
    if rxn_start is None or rxn_start < 0:
        st.warning("Please enter a valid reaction start time delay")
        st.stop()
    if "rxn_start" not in st.session_state:
        st.session_state.rxn_start = rxn_start
    if rxn_start != st.session_state.rxn_start:
        for key in [
            "gel_point",
            "y_gel_point",
            "gel_point_dosage",
            "fig2",
            "fig3"
        ]:
            st.session_state.pop(key, None)

        st.session_state.rxn_start = rxn_start


    # User input for intensity of run
    intensity = st.number_input(
        "Light Intensity (mW/cm²)",
        value=None,
        placeholder="Enter light intensity..."
    )
    if intensity is None or intensity <=0:
        st.warning("Please enter a valid light intensity before continuing")
        st.stop()

    if "last_intensity" not in st.session_state:
        st.session_state.last_intensity = intensity
    if intensity != st.session_state.last_intensity:
        # Clear results dependent on intensity
        for key in [
            "gel_point",
            "y_gel_point",
            "gel_point_dosage",
            "fig2",
            "fig3"
        ]:
            st.session_state.pop(key, None)

        st.session_state.last_intensity = intensity

    # Constants
    #rxn_start = 10
  


    #### File Processing ####
    @st.cache_data
    def process_file(uploaded_file,intensity):
         ########## Importing data from Trios Excel file ##########
        file = pd.ExcelFile(uploaded_file)
        sheet_names = file.sheet_names
        details = pd.read_excel(file,sheet_names[0])
        data = pd.read_excel(file,sheet_names[1],header=1)
        units = np.array(data.iloc[0])
        data = data.iloc[1:]

        
        ############# Data Processing ##################
        # Selecting data from pandas dataframe and converting to numpy array for processing
        storage_modulus = data['Storage modulus'].astype(float).to_numpy()
        loss_modulus = data['Loss modulus'].astype(float).to_numpy()
        step_time = data['Step time'].astype(float).to_numpy()
        dosage = (data['Step time']*intensity).astype(float).to_numpy()

        # Correcting for time shifts and adding dosage to table
        adjusted_step_time = step_time - rxn_start
        dosage = dosage - intensity*rxn_start
        adjusted_dosage = []
        for dose in dosage:
            if dose >= 0:
                adjusted_dosage.append(dose)
            else:
                adjusted_dosage.append(0)
        data['Dosage'] = adjusted_dosage
        units= np.append(units,'mW/cm²')

        # Adding Linear Interpolation Functions
        storage_interp_func = interp1d(step_time,storage_modulus)
        loss_interp_func = interp1d(step_time,loss_modulus)
        dosage_func = interp1d(step_time,dosage)

        return(data,units,storage_modulus,loss_modulus,step_time,adjusted_dosage,storage_interp_func,loss_interp_func,dosage_func)
   
    data,units,storage_modulus,loss_modulus,step_time,adjusted_dosage,storage_interp_func,loss_interp_func,dosage_func = process_file(uploaded_file,intensity)

    ########### Displays #############
    # Show table of data, including added dosage table
    # Additionally includes a dropdown table of units associated with each parameter
    st.subheader('File Data')
    show_table = st.checkbox("Show Table")
    if show_table:
        with st.expander("Table Units"):
            units_df = pd.DataFrame({
                "Column": data.columns,
                "Units": units
            })
            st.dataframe(units_df, hide_index=True)

        st.write(data)

    
    

    ### Plotting Data Points ###
    # Fig1 - G' and G" vs Step Time
    # Includes download .png button
    col1,col2 = st.columns(2)
    with col1:
    
        fig1,ax1 = plt.subplots(figsize=(5,4))
        ax1.scatter(step_time, storage_modulus,
                    color='green', s=10, label='Storage Modulus')
        ax1.scatter(step_time, loss_modulus,
                    color='blue', s=10, label='Loss Modulus')
        
        ax1.plot(
                [rxn_start,rxn_start],
                [min(storage_modulus), max(storage_modulus)],
                color='red',
                ls=':',
                alpha=0.5,
                label='Reaction Start'
            )

        ax1.set_yscale('log')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Modulus (MPa)')
        ax1.legend(loc='upper left',framealpha=1,fontsize=8)


        st.pyplot(fig1)

        buf1 = io.BytesIO()
        fig1.savefig(buf1, format="png",dpi=300,bbox_inches="tight")
        buf1.seek(0)

        st.download_button(
            'Download Raw Data Plot - Time',
            data=buf1,
            file_name=f"raw_plot_time_{base_name}.png",
            mime="image/png"
        )

    # Fig2 - G' and G" vs Dosage
    # Includes download .png button
    with col2:
        
        fig2, ax2 = plt.subplots(figsize=(5,4))
        ax2.scatter(adjusted_dosage, storage_modulus,
                    color='green', s=10, label='Storage Modulus')
        ax2.scatter(adjusted_dosage, loss_modulus,
                    color='blue', s=10, label='Loss Modulus')

        ax2.set_yscale('log')
        ax2.set_xlabel('Dosage (mJ/cm^2)')
        ax2.set_ylabel('Modulus (MPa)')
        ax2.legend(loc='upper left',framealpha=1,fontsize=8)


        st.pyplot(fig2)

        buf2 = io.BytesIO()
        fig2.savefig(buf2, format="png",dpi=300,bbox_inches="tight")
        buf2.seek(0)

        st.download_button(
            'Download Raw Data Plot - Dosage',
            data=buf2,
            file_name=f"raw_plot_dosage_{base_name}.png",
            mime="image/png"
        )


    ##### Gel Point Calculation and Display #####
    # Input for bounding the gel point
    # Uses the non adjusted, data recorded step time as seen in Fig1
    st.subheader("Gel Point Calculations")
    st.text('Using the time scale provided in plot above, input bounds for location of gel point')
    lower_bound = st.number_input("Lower bound for gel point search (seconds)")
    upper_bound = st.number_input("Upper bound for gel point search (seconds)")

    valid = (lower_bound < upper_bound and lower_bound > step_time[0] and upper_bound < step_time[-1])

    if lower_bound >= upper_bound:
        st.error("Lower bound must be less than Upper bound")
    if lower_bound <= step_time[0]:
        st.error("Lower bound must be greater than first timestep value")
    if upper_bound >= step_time[-1]:
        st.error("Upper bound must be less than last timestep value")


    # Button and actual calculation of Gel Point Time and Dosage
    calculate_gel = st.button("Calculate Gel Point",disabled=not valid)
    if calculate_gel:
        
        location_cross = [lower_bound,upper_bound]
        def solve_gel_point():
            def system(time):
                lhs = float(storage_interp_func(time)) - float(loss_interp_func(time))
                return lhs
            return root_scalar(system,bracket=location_cross,method='brentq').root

        gel_point = solve_gel_point()
        st.session_state.gel_point = gel_point

        y_gel_point = storage_interp_func(gel_point)
        st.session_state.y_gel_point = y_gel_point

        gel_point_dosage = dosage_func(gel_point)
        st.session_state.gel_point_dosage = gel_point_dosage

    # Displaying calculated gel point (time and dosage), ensuring only displayed if calculated
    # Then plots in Fig3 G' and G" vs step time WITH annotations of calculated gel point, and interpolation
    # used to calculate said gel point. With final option to download .png of graph
    if "gel_point" in st.session_state:
        gel_point = st.session_state.gel_point
        y_gel_point = st.session_state.y_gel_point
        gel_point_dosage = st.session_state.gel_point_dosage

        st.write(f"**Gel Point Time:** {gel_point-rxn_start:.3f} sec")
        st.write(f"**Gel Point Dosage:** {gel_point_dosage:.3f} mJ/cm²")

        left, center, right = st.columns([1,2,1])
        with center:
            fig3,ax3 = plt.subplots(figsize=(5,4))
            ax3.scatter(step_time, storage_modulus,
                color='green', s=10, label="G'")
            ax3.scatter(step_time, loss_modulus,
                    color='blue', s=10, label='G"')

            ax3.set_yscale('log')
            ax3.set_xlabel('Time (s)')
            ax3.set_ylabel('Modulus (MPa)')

            # Plot Gel Point
            ax3.scatter(gel_point, y_gel_point,
                    color='orange', label='Gel Point')

            ax3.annotate(
                f"Gel Point Time\n{gel_point-rxn_start:.3f} s",
                xy=(gel_point, y_gel_point),
                fontsize=8,
                xytext=(0.95,0.1),
                textcoords="axes fraction",
                ha="right",
                va="center",
                arrowprops=dict(
                    arrowstyle='->',
                    color='orange',
                    mutation_scale=10
                )
            )

            ax3.plot(
                [rxn_start,rxn_start],
                [min(storage_modulus), max(storage_modulus)],
                color='red',
                ls=':',
                alpha=0.5,
                label='Reaction Start'
            )

            # Plot Interpolation Lines
            time_axis = np.linspace(step_time[0], step_time[-1], 100)

            ax3.plot(
                time_axis,
                storage_interp_func(time_axis),
                color='green',
                ls='--',
                alpha=0.6,
                label="G' Interpolation"
            )

            ax3.plot(
                time_axis,
                loss_interp_func(time_axis),
                color='blue',
                ls='--',
                alpha=0.6,
                label='G" Interpolation'
            )

            ax3.legend(loc='upper left',framealpha=1,fontsize=8)

            st.pyplot(fig3)

            buf3 = io.BytesIO()
            fig3.savefig(buf3, format="png",dpi=300,bbox_inches="tight")
            buf3.seek(0)

            st.download_button(
                'Download Gel Point Plot',
                data=buf3,
                file_name=f"gel_point_plot_{base_name}.png",
                mime="image/png"
            )
