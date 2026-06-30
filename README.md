# Gel Point Calculator

A Streamlit application for calculating polymer gel points from rheology data. Specifically for photopolymerization reactions

## Description

This tool analyzes TRIOS rheometry Excel files and determines the gel point by finding the crossover between storage modulus (G') and loss modulus (G'').

## Features

- Upload TRIOS Excel rheology files
- Plot storage and loss modulus vs time
- Plot modulus vs dosage
- Calculate gel point using interpolation
- Export plots as PNG files

## Requirements

Python packages:
- streamlit
- numpy
- pandas
- matplotlib
- scipy
