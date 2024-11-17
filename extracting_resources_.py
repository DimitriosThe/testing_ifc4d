import ifcopenshell
import csv

"""
Minor Improvements (Optional)
Here are a few minor improvements that might make the code more robust:

Error Handling: You could add a try-except block around sections where attributes like NominalValue.wrappedValue are accessed to handle cases where NominalValue might not have a wrappedValue or is not set.

Redundant Quantity Extraction: Since the script currently loops twice over IfcRelDefinesByQuantity (once for general quantities and once for cost), you could combine these into a single loop to reduce redundancy.

Here is the optimized version with these improvements applied:

Apply a dictionarry to map the exported 

type_mapping = {
    "IfcCrewResource": "CREW",
    "IfcConstructionMaterialResource": "MATERIAL",
    "IfcConstructionProductResource": "PRODUCT",
    "IfcLaborResource": "LABOR",
    "IfcConstructionEquipmentResource": "EQUIPMENT",
    "IfcSubcontractResource": "SUBCONTRACT"


ADDED GUID export

ADDED HIERARCHY  CAPTURE
"""

# Load the IFC file
ifc_file = ifcopenshell.open(r"YOUR IFC FILE PATH AND FILE NAME")

# Define the CSV output file path
csv_output_path = r"THE CSV FILE PATH AND NAME"

# Dictionary for mapping IFC types to custom values
type_mapping = {
    "IfcCrewResource": "CREW",
    "IfcConstructionMaterialResource": "MATERIAL",
    "IfcConstructionProductResource": "PRODUCT",
    "IfcLaborResource": "LABOR",
    "IfcConstructionEquipmentResource": "EQUIPMENT",
    "IfcSubcontractResource": "SUBCONTRACT"
}

# Function to determine numeric hierarchy using IfcRelNests
def get_hierarchy_numeric(resource, level=1):
    """
    Recursively determine the numeric hierarchy level of a resource using IfcRelNests.
    
    Args:
        resource: The current IfcResource being analyzed.
        level: The current numeric hierarchy level (default: 1).
    
    Returns:
        The numeric hierarchy level (integer).
    """
    for rel_nests in ifc_file.by_type("IfcRelNests"):
        if rel_nests.RelatingObject == resource:
            # This resource is a parent
            return level
        if resource in rel_nests.RelatedObjects:
            # This resource is a child, increment level
            return get_hierarchy_numeric(rel_nests.RelatingObject, level + 1)
    # Default to top-level parent
    return level

# Open the CSV file for writing
with open(csv_output_path, mode="w", newline='', encoding="utf-8") as csv_file:
    csv_writer = csv.writer(csv_file)
    
    # Write the header row
    csv_writer.writerow([
        "GUID", "HIERARCHY", "TYPE", "ACTIVITY/RESOURCE NAME", "DESCRIPTION", 
        "COST", "USAGE", "UNIT", "QUANTITY NAME", "LABOR OUTPUT", 
        "EQUIPMENT OUTPUT", "Productivity Unit"
    ])
    
    # Loop through all resources in the IFC file
    for resource in ifc_file.by_type("IfcResource"):
        # Retrieve GUID
        guid = resource.GlobalId if resource.GlobalId else ""

        # Determine numeric hierarchy level
        hierarchy = get_hierarchy_numeric(resource)

        # Retrieve basic information
        raw_type = resource.is_a()  # Retrieve the raw IFC type
        type_ = type_mapping.get(raw_type, raw_type)  # Map the type or keep the original if not found
        name = resource.Name if resource.Name else ""
        description = resource.Description if resource.Description else ""
        
        # Initialize variables for extended properties
        cost = usage = unit = quantity_name = labor_output = equipment_output = productivity_unit = ""
        
        # Retrieve related properties and quantities
        for rel in resource.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                property_set = rel.RelatingPropertyDefinition
                if property_set.is_a("IfcPropertySet"):
                    for prop in property_set.HasProperties:
                        if prop.Name == "Cost":
                            cost = prop.NominalValue.wrappedValue if prop.NominalValue else ""
                        elif prop.Name == "BaseQuantityConsumed":
                            usage = prop.NominalValue.wrappedValue if prop.NominalValue else ""
                        elif prop.Name == "BaseQuantityProducedValue":
                            labor_output = prop.NominalValue.wrappedValue if prop.NominalValue else ""
                        elif prop.Name == "BaseQuantityProducedName":
                            quantity_name = prop.NominalValue.wrappedValue if prop.NominalValue else ""
                        
            elif rel.is_a("IfcRelDefinesByQuantity"):
                quantity_set = rel.RelatingQuantity
                if quantity_set.is_a("IfcElementQuantity"):
                    for quantity in quantity_set.Quantities:
                        if quantity.Name == "Base Quantity":
                            quantity_name = quantity.NominalValue.wrappedValue if quantity.NominalValue else ""
                        elif quantity.Name == "Labor Output":
                            labor_output = quantity.NominalValue.wrappedValue if quantity.NominalValue else ""
                        elif quantity.Name == "Equipment Output":
                            equipment_output = quantity.NominalValue.wrappedValue if quantity.NominalValue else ""
                        elif quantity.Name == "Unit":
                            unit = quantity.NominalValue.wrappedValue if quantity.NominalValue else unit
                        elif quantity.Name == "Cost":
                            cost = quantity.NominalValue.wrappedValue if quantity.NominalValue else cost

        # Look for direct cost information in IfcCostValue or related structure
        if getattr(resource, "BaseCosts", None):
            for cost_item in resource.BaseCosts:
                if cost_item.is_a("IfcCostValue"):
                    try:
                        cost = cost_item.AppliedValue.wrappedValue if cost_item.AppliedValue else ""
                    except AttributeError:
                        pass

        # Write the row to the CSV file
        csv_writer.writerow([
            guid, hierarchy, type_, name, description, cost, usage, unit, 
            quantity_name, labor_output, equipment_output, productivity_unit
        ])

print(f"Data successfully exported to {csv_output_path}")