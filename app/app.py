"""
Minimalist Docker Container Manager - Container List
"""
import streamlit as st


pages = [
    st.Page("pages/0_Container_manager.py", title="Containters", icon=":material/folder:", url_path="swe"),
    st.Page("pages/1_Download_Files.py", title="Download", icon=":material/dock_to_left:", url_path="containers"),
    st.Page("pages/2_Upload_Documents.py", title="Upload", icon=":material/folder:", url_path="config")
 ] 
    
pg = st.navigation(pages)
pg.run()

