### WIP ###
### Thesis abstract  - Torcuato Di Tella University @ Buenos Aires, Argentina.
Student: Joaquín Pablo Tempelsman
Tutor: Javier Marenco
Title: Application of Mixed-Integer Linear Optimization in the Argentine Agricultural Industry

### Motivation
In recent years, the intensive use of technology has been the main variable of change in multiple industries. Agriculture has also been a fertile ground for innovation, particularly in the Argentine context. Since the 90s, the use of technology has allowed increasing the yield per hectare year after year, reaching levels of the international production efficiency frontier. However, many business decisions are still made without giving central importance to data. The use of analytical techniques for decision-making still has significant value to add to the business. Therefore, the development of analytical tools and approaches in this industry will have a double challenge, both in the design and adoption of the solution. This makes the opportunities to capture value potentially greater, especially if we manage to create prescriptive analysis (i.e., systematically integrated into decision-making).

Linear programming (LP) models are a versatile tool applicable to multiple contexts and have proven to be useful for making data-driven decisions. Within an LP model, we can consider multiple business variables and limit them by a series of constraints to maximize the productive yield in a given intertemporal horizon. The use of these models in the field of agricultural production has a broad scope worldwide. In Argentina, we find several publications with solutions of this type, such as models that analyze multiple livestock breeding schemes, horticultural production and distribution, and optimization models for land use.

### Thesis Objective
The project aims to provide prescriptive solutions to an Argentine agricultural company. Several questions arose from the company's management that are central to the business. Some of these questions were: "When is it convenient to sell?" or "What kind of product should we develop and when?" "Lease or directly exploit the land?" "What level and type of livestock stock is convenient to accumulate?" Many of these questions found an answer based on business experience and future expectations. Although quantitative information was added to the decision-making process, data was not intensively used.

Through an analysis of the current productive matrix, I will seek to model the relevant business variables in an intertemporal decision scheme that maximizes the profit of the available resources. The model will seek to add a tool to the decision-making process and approach several of the questions posed by the company. One of the main decisions to model is when to sell the product, and therefore, when to start breeding, also evaluating early or late sale (with greater fattening) of the animals. In the second plan, part of the business is devoted to cultivation; therefore, some decisions must consider the type of crop, costs, cultivation time, storage, and sale according to future price expectations. We will also consider decisions such as outsourcing breeding processes or not, fattening livestock or selling them at an early stage, variable costs of labor required according to the productive scheme, etc.

We must also consider uncertainty in both supply and demand. Productive yield is not linear since we consider livestock breeding as the result of multiple quantifiable and non-quantifiable dimensions. We will also have uncertainty in the future prices of the different products. We will also consider modeling different possible scenarios where we will consider the impact of the climate or even commercial policy regulations by the state.

### Data
The main source of data will be the reports prepared by the company semi-annually. They detail historical information on the various production lines. There is also a breakdown of costs incurred in each activity. Another source of data will be international selling prices, the current tax regime, and relevant macroeconomic variables.

### Methodology
The methodology will consist of using past decisions and their results as benchmarks. We will model one or more of these periods and compare the performance per hectare, thus achieving a validation scheme for the solution. The metric we will seek to improve is the net profit obtained per hectare compared to the benchmark of previous years.

After optimization, a potential sensitivity analysis and feasibility of the results will be added, particularly considering the impact of changes in climate and commercial and export policy regulations.

### Project key files 
[Zimpl script](https://github.com/joaquin-tempelsman/thesis_lp_utdt_mim/blob/main/modelo.zpl)
[Utilitary notebook to build model inputs](https://github.com/joaquin-tempelsman/thesis_lp_utdt_mim/blob/main/build_inputs.ipynb)
[EDA noteboook of model outputs](https://github.com/joaquin-tempelsman/thesis_lp_utdt_mim/blob/main/read_log.ipynb)

