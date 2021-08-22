# Mercado Bitcoin Utils

## IMPORTANT: DISCLAIMER
It goes without saying that, **specially** since we are dealing with real money, the usage of this package is intended for 
**YOUR OWN RISK**. I'll give absolutely NO GUARANTIES that it won't spend all the money you may have at the same site.
I am using this for my unique understanding of ML algorithms and some proper fun.

## Introduction

This packed is intended to achieve 3 main things:
1. Control of the APIs of the website [Mercado Bitcoin](https://www.mercadobitcoin.com.br/).
2. Basic Machine Learning (ML) analysis and prediction of Bitcoin with public (or private) data from the same site.
3. Learning ground for some ML algorithms.


## Installation

## Configuration
To configure, you need to create a .ini file with the following parameters:

    [MercadoBitcoin]
    BaseUrl = https://www.mercadobitcoin.net
    TapiID = None
    TapiSecret = None
    
    [Log]
    FileStream =  logs/mercadoBTC.log
    Level = DEBUG

And you can either:
1. Create a system variable named MERCADOBTC_CFG_FILE with the path of the ini file, or
2. Create the file named `mercadoBTC.ini` on your current directory you are calling this package

If the configuration file does not exist, it'll assume the default values (the ones on the sample here)

## Basic Usage

## Machine Learning Analysis
