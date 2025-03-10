import xmltodict
import os
import glob
"""
Author: Valentina Matos (Johns Hopkins - Wirtz/Kiemen Lab)
Date: March 10th, 2025
"""

def swap_layers_by_names(base_path, layer_names, positions, case_sensitive=True):
    '''
    This function processes XML files to swap specified layers by names into designated positions, moving the rest of the layers one place down.

    Inputs:
    - base_path (str): The file location of the XML files.
    - layer_names (list): A list of names of the layers to swap.
    - positions (list): A list of positions to swap the layers into.
    - case_sensitive (bool): Whether the layer name matching should be case sensitive. Default is True.

    Outputs:
    - None: The function saves the modified XML files in a new directory and prints confirmation messages. If a specified layer name is not found or is already in the specified position, it skips the file and displays an error message.
    '''

    if len(layer_names) != len(positions):
        raise ValueError("The length of layer_names and positions must be the same.")

    # Find all XML files in the specified directory
    xml_files = glob.glob(os.path.join(base_path, "*.xml"))

    # Create output directory
    new_folder = os.path.join(base_path, "new xml")
    os.makedirs(new_folder, exist_ok=True)

    for xml_file in xml_files:
        with open(xml_file, 'r') as file:
            xml_dict = xmltodict.parse(file.read())

        layers = xml_dict["Annotations"]["Annotation"]
        filename = os.path.basename(xml_file)
        modified = False
        already_correct = True

        for layer_name, position in zip(layer_names, positions):
            # Find the layer by name
            layer_to_swap = None
            for idx, layer in enumerate(layers):
                layer_name_to_compare = layer['@Name'] if case_sensitive else layer['@Name'].lower()
                target_name_to_compare = layer_name if case_sensitive else layer_name.lower()
                if layer_name_to_compare == target_name_to_compare:
                    if idx == position:
                        print(f"Layer '{layer_name}' is already in position {position} in file: {filename}")
                        break
                    layer_to_swap = layer
                    already_correct = False
                    break

            if layer_to_swap is None:
                if idx != position:
                    print(f"Error: Layer '{layer_name}' not found in file: {filename}")
                continue

            # Remove the layer from its current position
            layers.remove(layer_to_swap)

            # Insert the layer at the specified position
            layers.insert(position, layer_to_swap)
            modified = True

        if modified:
            # Create new XML structure
            xml_dict["Annotations"]["Annotation"] = layers

            # Save the modified XML file
            new_xmlpath = os.path.join(new_folder, filename)
            with open(new_xmlpath, 'w') as file:
                file.write(xmltodict.unparse(xml_dict, pretty=True))

            print(f"{filename} modified successfully ({xml_files.index(xml_file) + 1}/{len(xml_files)})")
        elif already_correct:
            print(f"({xml_files.index(xml_file) + 1}/{len(xml_files)})")

if __name__ == "__main__":
    base_path = r'\\10.99.68.52\Kiemendata\Valentina Matos\LG HG PanIN project\annotations lucie to revise'
    layer_names = ['stroma', 'epithelium']
    positions = [2, 3]
    swap_layers_by_names(base_path, layer_names, positions, case_sensitive=False)