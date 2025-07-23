import xmltodict
import os
import glob
import tkinter as tk
from tkinter import messagebox

def reorder_layers(base_path, layer_names, case_sensitive=False):
    '''
    Reorder layers in XML files, saving only if the layer order/names match,
    or if there are extra layers and user chooses to save.
    '''
    # Find all XML files in the specified directory
    xml_files = glob.glob(os.path.join(base_path, "*.xml"))

    # Create output directory
    output_folder = os.path.join(base_path, "reordered_xml")
    os.makedirs(output_folder, exist_ok=True)

    # For user prompts; re-create/destroy per box to avoid Tkinter hang
    def ask_mismatch(message, kind='yesno'):
        root = tk.Tk()
        root.withdraw()
        if kind == 'yesno':
            result = messagebox.askyesno("Layer Order Mismatch", message, master=root)
        elif kind == 'custom':
            result = custom_buttons(message, root)
        root.destroy()
        return result

    def custom_buttons(message, root):
        # Custom dialog for extra layers
        result = {'choice': None}
        win = tk.Toplevel(root)
        win.geometry("520x500")
        win.title("Layer Mismatch")
        label = tk.Label(win, text=message, wraplength=500, justify="left")
        label.pack(pady=10, padx=5)

        def _sc(c):
            result['choice'] = c
            win.destroy()
        btn1 = tk.Button(win, text="Save and Continue", command=lambda: _sc('save'))
        btn2 = tk.Button(win, text="Continue Without Saving", command=lambda: _sc('skip'))
        btn3 = tk.Button(win, text="Stop Execution", command=lambda: _sc('stop'))
        btn1.pack(pady=5)
        btn2.pack(pady=5)
        btn3.pack(pady=5)
        win.wait_window()
        return result['choice']

    # Normalize layer names for matching
    normalized_layer_names = [
        [name if case_sensitive else name.lower() for name in (layer if isinstance(layer, list) else [layer])]
        for layer in layer_names
    ]
    expected_layer_count = len(normalized_layer_names)

    for k, xml_file in enumerate(xml_files):

        print(f'Processing file: {xml_file} {k+1}/{len(xml_files)}')
        with open(xml_file, 'r', encoding='utf-8') as file:
            xml_dict = xmltodict.parse(file.read())

        layers = xml_dict["Annotations"]["Annotation"]
        if not isinstance(layers, list):
            layers = [layers]

        # get original layer names
        original_layer_names = [layer['@Name'] for layer in layers if isinstance(layer, dict) and '@Name' in layer]
        filename = os.path.basename(xml_file)

        # Reorder layers based on normalized names
        found_layers = []
        used_indices = set()
        for target_names in normalized_layer_names:
            matched_layer = None
            for idx, layer in enumerate(layers):
                if idx in used_indices: continue
                layer_name = layer['@Name']
                normalized = layer_name if case_sensitive else layer_name.lower()
                if normalized in target_names:
                    matched_layer = layer
                    used_indices.add(idx)
                    break
            found_layers.append(matched_layer)
        # Remove found layers from original
        rest_layers = [layer for idx, layer in enumerate(layers) if idx not in used_indices]
        # Build final reordered layer list (matched, then extra)
        reordered_layers = [layer for layer in found_layers if layer is not None] + rest_layers

        # Sanity names for display
        processed_order = [layer['@Name'] if layer else None for layer in found_layers]
        final_order = [layer['@Name'] for layer in reordered_layers]
        expected_names = ['/'.join(names) for names in normalized_layer_names]

        save_file = False  # will ONLY be set to True on proper match or save-and-continue
        # Layer count matches, all matched
        exact_match = (all(layer is not None for layer in found_layers)
                      and len(layers) == len(normalized_layer_names)
                      and processed_order == original_layer_names)
        # Reordered but exact selection
        exact_diff_order = (all(layer is not None for layer in found_layers)
                            and len(layers) == len(normalized_layer_names)
                            and processed_order != original_layer_names)
        # File has too few layers
        too_few_layers = any(layer is None for layer in found_layers)
        # File has extra layers (all matched, but longer file):
        extra_layers = all(layer is not None for layer in found_layers) and len(layers) > len(normalized_layer_names)

        # Save if: names match and order matches
        if exact_match:
            save_file = True
        elif too_few_layers:
            # Too few layers: prompt, don't save
            message = (
                f"File: {filename}\n\n"
                f"File has fewer layers than expected.\n\n"
                f"Target Layers:\n{expected_names}\n\n"
                f"Layers in File:\n{original_layer_names}\n\n"
                f"After Processing:\n{processed_order}\n\n"
                "Continue with next file?"
            )
            result = ask_mismatch(message, kind='yesno')
            if not result:
                print("Execution stopped by user.")
                return
            continue
        elif extra_layers:
            # More layers than expected
            message = (
                f"File: {filename}\n\n"
                f"File has more layers than expected.\n\n"
                f"Target Layers:\n{expected_names}\n\n"
                f"Layers in File:\n{original_layer_names}\n\n"
                f"Final Layer Order (after processing):\n{final_order}\n\n"
                "The extra layers will be positioned last.\n\n"
                "Choose an action:"
            )
            result = ask_mismatch(message, kind='custom')
            if result == 'save':
                save_file = True
            elif result == 'skip':
                continue
            elif result == 'stop':
                print("Execution stopped by user.")
                return
        elif exact_diff_order:
            # Same count, reordered: prompt, don't save
            message = (
                f"File: {filename}\n\n"
                f"The file has the same number of layers as target, but the order does not match.\n\n"
                f"Target Order:\n{expected_names}\n\n"
                f"File Order:\n{original_layer_names}\n\n"
                f"After Processing:\n{processed_order}\n\n"
                "Continue with next file?"
            )
            result = ask_mismatch(message, kind='yesno')
            if not result:
                print("Execution stopped by user.")
                return
            continue
        else:
            # Other unhandled edge case
            continue

        if save_file:
            xml_dict["Annotations"]["Annotation"] = reordered_layers
            new_xml_path = os.path.join(output_folder, filename)
            with open(new_xml_path, 'w', encoding='utf-8') as file:
                file.write(xmltodict.unparse(xml_dict, pretty=True))
            print(f"{filename} processed successfully ({k + 1}/{len(xml_files)})")

if __name__ == "__main__":
    base_path = r'\\10.99.68.52\Kiemendata\Valentina Matos\LG HG PanIN project\LGHG segmentation'
    layer_names = [
        ['islet', 'islets'], ['duct', 'ducts','normal duct'], ['vasculature', 'blood vessel'], ['fat'], ['acini'] , ['ecm', 'stroma'], ['whitespace'],
        ['LG Panin', 'panin'], ['noise'], ['nerve', 'nerves'], ['endo', 'endothelium'],
        ['immune'], ['PDAC'], ['HG panin'], ['PanIN 2.5']
    ]  # 15 layers
    reorder_layers(base_path, layer_names, case_sensitive=False)