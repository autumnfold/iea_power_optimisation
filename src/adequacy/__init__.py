"""Domestic electricity adequacy model for France, 2019 vs 2022.

Specification: ``docs/adequacy_model.md``. Modules, in the order the data flows:

- ``data``: load one year of RTE eCO2mix data and check its conventions;
- ``inputs``: build the two drivers' inputs (net demand and hydro budgets; availability);
- ``allocation``: place the flexible hydro energy (water-filling, and a reference LP);
- ``scenarios``: run the four scenarios and attribute the change (``shapley``);
- ``checks``: physical-consistency checks, Test B and the import comparison;
- ``run``: command-line entry point that writes the results.
"""
