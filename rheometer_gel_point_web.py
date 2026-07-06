import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import interp1d
from scipy.optimize import root_scalar
import io
from pathlib import Path
import plotly.graph_objects as go


##### Title Header ####
st.set_page_config(page_title="Gel Point Calculator",
                   page_icon="🧪",
                   layout="wide")

st.title("🧪 Gel Point Calculator")

tab1, tab2, tab3, tab4 = st.tabs([
    "Sample 1",
    "Sample 2",
    "Sample 3",
    "Comparison"
])

@st.cache_data
def load_file(file_bytes):
    file = pd.ExcelFile(io.BytesIO(file_bytes))
    sheet_names = file.sheet_names
    
    data = pd.read_excel(file,sheet_names[1],header=1)
    units = np.array(data.iloc[0])
    data = data.iloc[1:]

    data["Storage modulus"] = data["Storage modulus"].astype(float)
    data["Loss modulus"] = data["Loss modulus"].astype(float)
    data["Step time"] = data["Step time"].astype(float)

    return data, units


def process_data(data, intensity, rxn_start):

    storage_modulus = data["Storage modulus"].to_numpy()
    loss_modulus = data["Loss modulus"].to_numpy()
    step_time = data["Step time"].to_numpy()

    dosage = step_time * intensity
    dosage = np.maximum(dosage - intensity * rxn_start,0)

    data = data.copy()
    data["Dosage"] = dosage

    storage_interp_func = interp1d(step_time, storage_modulus)
    loss_interp_func = interp1d(step_time, loss_modulus)
    dosage_func = interp1d(step_time, dosage)

    return (
        data,
        step_time,
        storage_modulus,
        loss_modulus,
        dosage,
        storage_interp_func,
        loss_interp_func,
        dosage_func,
    )


@st.cache_data
def create_time_plot(step_time, storage_modulus, loss_modulus, rxn_start):
    fig,ax = plt.subplots(figsize=(5,4))
    ax.scatter(step_time, storage_modulus,
                color='green', s=10, label='Storage Modulus')
    ax.scatter(step_time, loss_modulus,
                color='blue', s=10, label='Loss Modulus')
    
    ax.plot(
            [rxn_start,rxn_start],
            [min(storage_modulus), max(storage_modulus)],
            color='red',
            ls=':',
            alpha=0.5,
            label='Reaction Start'
        )

    ax.set_yscale('log')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Modulus (MPa)')
    ax.legend(loc='upper left',framealpha=1,fontsize=8)

    return fig


@st.cache_data
def create_dosage_plot(adjusted_dosage, storage_modulus, loss_modulus):
    fig, ax = plt.subplots(figsize=(5,4))
    ax.scatter(adjusted_dosage, storage_modulus,
                color='green', s=10, label='Storage Modulus')
    ax.scatter(adjusted_dosage, loss_modulus,
                color='blue', s=10, label='Loss Modulus')

    ax.set_yscale('log')
    ax.set_xlabel('Dosage (mJ/cm^2)')
    ax.set_ylabel('Modulus (MPa)')
    ax.legend(loc='upper left',framealpha=1,fontsize=8)

    return fig

def create_gel_point_plot(step_time, storage, loss, rxn_start,
                          gel_time, gel_dose, storage_i, loss_i):

    fig,ax = plt.subplots(figsize=(5,4))
    ax.scatter(step_time, storage,
        color='green', s=10, label="G'")
    ax.scatter(step_time, loss,
            color='blue', s=10, label='G"')

    ax.set_yscale('log')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Modulus (MPa)')

    # Plot Gel Point
    ax.scatter(gel_time+rxn_start, storage_i(gel_time+rxn_start),
            color='orange', label='Gel Point')

    ax.annotate(
        f"Gel Point Time\n{gel_time:.3f} s",
        xy=(gel_time+rxn_start, storage_i(gel_time+rxn_start)),
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

    ax.plot(
        [rxn_start,rxn_start],
        [min(storage), max(storage)],
        color='red',
        ls=':',
        alpha=0.5,
        label='Reaction Start'
    )

    # Plot Interpolation Lines
    time_axis = np.linspace(step_time[0], step_time[-1], 100)

    ax.plot(
        time_axis,
        storage_i(time_axis),
        color='green',
        ls='--',
        alpha=0.6,
        label="G' Interpolation"
    )

    ax.plot(
        time_axis,
        loss_i(time_axis),
        color='blue',
        ls='--',
        alpha=0.6,
        label='G" Interpolation'
    )

    ax.legend(loc='upper left',framealpha=1,fontsize=8)

    return fig



def combine_plot_modulus_vs_time(sample_dictionary_array):
    fig,ax = plt.subplots(figsize=(5,4))
    index = 1
    for sample_dict in sample_dictionary_array:
        rxn_start = sample_dict['rxn_start']
        step_time = sample_dict['step_time']
        storage_modulus = sample_dict['storage']
        loss_modulus = sample_dict['loss']
        ax.scatter(step_time, storage_modulus,
                    s=10, label=f'G\' S{index}')
        ax.scatter(step_time, loss_modulus,
                    s=10, label=f'G\" S{index}')
        
        index += 1

    ax.plot(
                [rxn_start,rxn_start],
                [min(storage_modulus), max(storage_modulus)],
                color='red',
                ls=':',
                alpha=0.5,
                label='Rxn Start'
            )

    ax.set_yscale('log')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Modulus (MPa)')
    ax.legend(loc='upper left',framealpha=1,fontsize=8)

    return fig

def combine_plot_modulus_vs_dosage(sample_dictionary_array):
    fig,ax = plt.subplots(figsize=(5,4))
    index = 1
    for sample_dict in sample_dictionary_array:
        dosage = sample_dict['dosage']
        storage_modulus = sample_dict['storage']
        loss_modulus = sample_dict['loss']
        ax.scatter(dosage, storage_modulus,
                    s=10, label=f'G\' S{index}')
        ax.scatter(dosage, loss_modulus,
                    s=10, label=f'G\" S{index}')
        
        index += 1

    ax.set_yscale('log')
    ax.set_xlabel('Dosage (mJ/cm^2)')
    ax.set_ylabel('Modulus (MPa)')
    ax.legend(loc='upper left',framealpha=1,fontsize=8)

    return fig


def make_download_image_button(fig, filename, button_text, key):

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    buf.seek(0)

    st.download_button(
        button_text,
        data=buf,
        file_name=filename,
        mime="image/png",
        key=key
    )



def make_download_table_button(df, filename, button_text, key):

    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    buffer.seek(0)

    st.download_button(
        button_text,
        data=buffer,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=key
    )


@st.cache_data
def build_bundle(file_bytes, intensity, rxn_start):

    data, units = load_file(file_bytes)

    data, step_time, storage, loss, dosage, storage_i, loss_i, dosage_i = process_data(
        data, intensity, rxn_start
    )

    fig_time = create_time_plot(step_time, storage, loss, rxn_start)
    fig_dosage = create_dosage_plot(dosage, storage, loss)

    return {
        "step_time": step_time,
        "storage": storage,
        "loss": loss,
        "dosage": dosage,
        "storage_i": storage_i,
        "loss_i": loss_i,
        "dosage_i": dosage_i,
        "fig_time": fig_time,
        "fig_dosage": fig_dosage,
        "units": units,
        "rxn_start": rxn_start,
        "data":data
    }


def sample_tab(tab_name):
    uploaded_file = st.file_uploader(
        "Upload a TRIOS Excel file",
        type=["xls"],
        key=f"{tab_name}_upload"
    )

    if uploaded_file is None:
        return None
    
    # User input for intensity of run
    intensity = st.number_input(
        "Light Intensity (mW/cm²)",
        value=5,
        placeholder="Enter light intensity...",
        key = f"{tab_name}_intensity"
    )

    rxn_start = st.number_input(
        "Rxn Start - Time Delay (s)",
        value = 10,
        key = f"{tab_name}_rxn_start"
    )

    signature = (
        intensity,
        rxn_start,
        uploaded_file.name if uploaded_file else None
    )

    prev_signature = st.session_state.get(f"{tab_name}_signature")

    if prev_signature != signature:
        st.session_state.pop(f"{tab_name}_gel", None)
        st.session_state.pop(f"{tab_name}_bundle", None)
        st.session_state.pop("tab4_cache", None)

    st.session_state[f"{tab_name}_signature"] = signature


    file_id = (uploaded_file.name, uploaded_file.size)
    file_bytes = uploaded_file.getvalue()
    bundle = build_bundle(file_bytes,intensity,rxn_start)
        
    st.session_state[f"{tab_name}_bundle"] = bundle


    col1,col2 = st.columns(2)
    with col1:
        st.pyplot(bundle["fig_time"])
        make_download_image_button(
            bundle["fig_time"],
            f"{tab_name}_time.png",
            "Download Time Plot",
            f"{tab_name}_time_download"
        )
    with col2:
        st.pyplot(bundle["fig_dosage"])
        make_download_image_button(
            bundle["fig_dosage"],
            f"{tab_name}_dosage.png",
            "Download Dosage Plot",
            f"{tab_name}_dose_download"
        )
    


    st.subheader("File Data")

    show_table = st.checkbox("Show Table", key=f"{tab_name}_show_table")

    if show_table:

        data = bundle["data"]
        units = bundle["units"]
        units = np.append(units,'mW/cm²')

        st.dataframe(data, use_container_width=True)
        with st.expander("Table Units"):

            units_df = pd.DataFrame({
                "Column": data.columns,
                "Units": units
            })

            st.dataframe(units_df, hide_index=True)

        make_download_table_button(
            pd.concat([pd.DataFrame([units],columns=data.columns),data],ignore_index=True),
            f"{tab_name}_processed.xlsx",
            "Download Processed Data",
            f"{tab_name}_excel_download"
        )



    st.subheader("Gel Point Calculations")
    st.text('Using the time scale provided in plot above, input bounds for location of gel point')
    
    result_placeholder = st.container()

    with st.form(f"{tab_name}_gel_form"):
        lower_bound = st.number_input("Lower bound for gel point search (seconds)",key=f"{tab_name}_lower_bound")
        upper_bound = st.number_input("Upper bound for gel point search (seconds)",key=f"{tab_name}_upper_bound")

        submitted = st.form_submit_button("Calculate Gel Point")
    
    
    if submitted:

        storage_i = bundle["storage_i"]
        loss_i = bundle["loss_i"]

        def diff_storage_loss(t):
            return float(storage_i(t)) - float(loss_i(t))
        
        root = root_scalar(diff_storage_loss,bracket=[lower_bound,upper_bound]).root

        gel_time = root - rxn_start
        gel_dose = bundle['dosage_i'](root)
        
        result_placeholder.empty()
        
        fig3 = create_gel_point_plot(
        bundle["step_time"],
        bundle["storage"],
        bundle["loss"],
        bundle["rxn_start"],
        gel_time,
        gel_dose,
        storage_i,
        loss_i
    )

        st.session_state[f"{tab_name}_gel"] = {
            "time": gel_time,
            "dose": gel_dose,
            "fig3": fig3
        }

    gel_state = st.session_state.get(f"{tab_name}_gel")

    if gel_state:

        st.success(f"Gel Time: {gel_state['time']:.3f} s")
        st.success(f"Gel Dose: {gel_state['dose']:.3f} mJ/cm²")
        left, center, right = st.columns([1,2,1])
        with center:
            st.pyplot(
                gel_state["fig3"]
            )
            make_download_image_button(
                gel_state["fig3"],
                f"{tab_name}_gel_point.png",
                "Download Annotated Gel Time Plot",
                f"{tab_name}_gel_point_plot"
            )

    else:
        bundle["gel_time"] = None
        bundle["gel_value"] = None

    return bundle
            








with tab1:
    s1 = sample_tab("s1")
with tab2:
    s2 = sample_tab("s2")
with tab3:
    s3 = sample_tab("s3")


with tab4:
    samples = [s for s in [s1, s2, s3] if s is not None]


    if samples:
        st.subheader("Comparison Plots")
        col1,col2 = st.columns(2)
        with col1:   
            fig_combine_time = combine_plot_modulus_vs_time(samples)
            st.pyplot(fig_combine_time)
            make_download_image_button(
                fig_combine_time,
                f"combined_time.png",
                "Download Combined Time Plot",
                f"combined_time_download"
            )
        with col2:
            fig_combine_dose = combine_plot_modulus_vs_dosage(samples)
            st.pyplot(fig_combine_dose)
            make_download_image_button(
                fig_combine_dose,
                f"combined_dose.png",
                "Download Combined Dosage Plot",
                f"combined_dose_download"
            )

        sum_gel_point_time, sum_gel_point_dosage = [0,0]
        samples_averaged = 0
        count = 0
        sample_names = []
        gel_point_values = []
        gel_point_dosages = []
        
        gel_keys = [k for k in st.session_state.keys() if k.endswith("_gel")]

        for i, key in enumerate(gel_keys, start=1):

            sample_names.append(f"Sample {i}")

            gel_state = st.session_state.get(key)

            if gel_state is not None:

                t = gel_state["time"]
                d = gel_state["dose"]

                gel_point_values.append(round(float(t), 3))
                gel_point_dosages.append(round(float(d), 3))

                sum_gel_point_time += t
                sum_gel_point_dosage += d
                samples_averaged += 1

            else:
                gel_point_values.append("---")
                gel_point_dosages.append("---")

        st.subheader(f'Average Calculations')
        st.write(f'Using {samples_averaged} of the {len(samples)} samples provided')
        if samples_averaged >= 1:
            average_gel_point_time = round(sum_gel_point_time/samples_averaged,3)
            average_gel_point_dosage = round(sum_gel_point_dosage/samples_averaged,3)

            st.write(f"**Average Gel Point Time:** {average_gel_point_time} sec")
            st.write(f"**Average Gel Point Dosage:** {average_gel_point_dosage} mJ/cm²")
        
        else:
            average_gel_point_time = '---'
            average_gel_point_dosage = '---'

            st.write(f"**Average Gel Point Time:** NOT CALCULATED")
            st.write(f"**Average Gel Point Dosage:** NOT CALCULATED")


        st.text(f'* Please ensure that you calculate gel point on the tab associated with each sample dataset.  \n' +
                f'   If not, the sample data\'s gel point will NOT be included in calculating the average gel point')


        st.subheader("Table of Calculated Gel Points")
        gel_points_df = pd.DataFrame({
            "Sample": sample_names,
            "Gel Point Time (s)": gel_point_values,
            "Gel Point Dosage (mW/cm²)": gel_point_dosages
        })
        st.dataframe(gel_points_df,hide_index=True)

        export_gel_points_df = gel_points_df.copy()
        export_gel_points_df.loc[len(export_gel_points_df)] = {
            "Sample": "Average",
            "Gel Point Time (s)": average_gel_point_time,
            "Gel Point Dosage (mW/cm²)": average_gel_point_dosage}


        make_download_table_button(
            export_gel_points_df,
            f"gel_point_data.xlsx",
            "Download Gel Point Table",
            f"gel_point_excel_download"
        )




