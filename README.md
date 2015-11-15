# PacH 
_Lucio Nardelli - Director Hernán Ponce de León_

 Parse logs (as XES or TXT File) and calculate the minimum convex hull using Pyhull (https://pythonhosted.org/pyhull)
 of the  Parikh's vector of the the events in the traces.

 We use two different high-level techniques to handle large logs: projection and sampling

 After getting the convex hull, some automatic simplifications are made in order to get a "nicer" model.
 
 As a final step, the resuilting PNML is generated according to the international standard.
 
