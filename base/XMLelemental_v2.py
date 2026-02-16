import xmltodict
import os
import glob
import tkinter as tk
from tkinter import messagebox
import re


def natural_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]


def reorder_layers(base_path, layer_names, case_sensitive=False):

    xml_files = glob.glob(os.path.join(base_path, "*.xml"))
    xml_files = sorted(xml_files,
                       key=lambda x: natural_key(os.path.basename(x)))

    output_folder = os.path.join(base_path, "reordered_xml")
    os.makedirs(output_folder, exist_ok=True)

    # ---------- UI Dialog ----------

    def show_custom_dialog(title, message):
        root = tk.Tk()
        root.withdraw()

        result = {"choice": None}

        win = tk.Toplevel(root)
        win.title(title)
        win.geometry("720x600")
        win.configure(bg="white")

        frame = tk.Frame(win, bg="white", padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        label = tk.Label(
            frame,
            text=message,
            justify="left",
            wraplength=660,
            bg="white",
            anchor="w"
        )
        label.pack(fill="both", expand=True)

        button_frame = tk.Frame(frame, bg="white")
        button_frame.pack(pady=15)

        def select(choice):
            result["choice"] = choice
            win.destroy()

        tk.Button(button_frame, text="Save and Continue",
                  width=20, command=lambda: select("save")).pack(side="left", padx=10)
        tk.Button(button_frame, text="Skip File",
                  width=15, command=lambda: select("skip")).pack(side="left", padx=10)
        tk.Button(button_frame, text="Stop Execution",
                  width=15, command=lambda: select("stop")).pack(side="left", padx=10)

        win.wait_window()
        root.destroy()
        return result["choice"]

    # ---------- Aperio Layer Template ----------

    def create_empty_layer(layer_name, new_id, line_color="65280"):
        return {
            '@Id': str(new_id),
            '@Name': layer_name,
            '@ReadOnly': '0',
            '@NameReadOnly': '0',
            '@LineColorReadOnly': '0',
            '@Incremental': '0',
            '@Type': '4',
            '@LineColor': str(line_color),
            '@Visible': '1',
            '@Selected': '0',
            '@MarkupImagePath': '',
            '@MacroName': '',
            'Attributes': {
                'Attribute': {
                    '@Name': 'Description',
                    '@Id': '0',
                    '@Value': ''
                }
            },
            'Regions': {
                'RegionAttributeHeaders': {
                    'AttributeHeader': [
                        {'@Id': '9999', '@Name': 'Region', '@ColumnWidth': '-1'},
                        {'@Id': '9997', '@Name': 'Length', '@ColumnWidth': '-1'},
                        {'@Id': '9996', '@Name': 'Area', '@ColumnWidth': '-1'},
                        {'@Id': '9998', '@Name': 'Text', '@ColumnWidth': '-1'},
                        {'@Id': '1', '@Name': 'Description', '@ColumnWidth': '-1'}
                    ]
                }
            },
            'Plots': None
        }

    # ---------- Normalize Target Names ----------

    normalized_layer_names = [
        [name if case_sensitive else name.lower()
         for name in (layer if isinstance(layer, list) else [layer])]
        for layer in layer_names
    ]

    expected_layer_count = len(layer_names)

    # ---------- Process Files ----------

    for file_index, xml_file in enumerate(xml_files):

        filename = os.path.basename(xml_file)
        print(f"\nProcessing {file_index + 1}/{len(xml_files)}: {filename}")

        with open(xml_file, 'r', encoding='utf-8') as file:
            xml_dict = xmltodict.parse(file.read())

        layers = xml_dict["Annotations"]["Annotation"]

        if not isinstance(layers, list):
            layers = [layers]

        original_layer_names = [
            layer['@Name'] for layer in layers if '@Name' in layer
        ]

        # Determine starting ID for new layers
        existing_ids = [
            int(layer['@Id']) for layer in layers if '@Id' in layer
        ]
        next_id = max(existing_ids) + 1 if existing_ids else 1

        found_layers = []
        used_indices = set()

        # ---------- Reorder + Add Missing ----------

        for target_index, target_names in enumerate(normalized_layer_names):

            matched_layer = None

            for idx, layer in enumerate(layers):
                if idx in used_indices:
                    continue

                layer_name = layer['@Name']
                normalized = layer_name if case_sensitive else layer_name.lower()

                if normalized in target_names:
                    matched_layer = layer
                    used_indices.add(idx)
                    break

            if matched_layer is None:
                canonical_name = layer_names[target_index][0]
                matched_layer = create_empty_layer(canonical_name, next_id)
                next_id += 1

            found_layers.append(matched_layer)

        # Keep extra layers after target ones
        rest_layers = [
            layer for idx, layer in enumerate(layers)
            if idx not in used_indices
        ]

        reordered_layers = found_layers + rest_layers

        final_order = [layer['@Name'] for layer in reordered_layers]
        expected_names = [names[0] for names in layer_names]

        # ---------- UI Notice If Mismatch ----------

        if len(original_layer_names) != expected_layer_count:

            message = (
                f"File: {filename}\n\n"
                f"Expected {expected_layer_count} layers\n"
                f"Found {len(original_layer_names)} layers\n\n"
                f"Expected Order:\n{expected_names}\n\n"
                f"Original Layers:\n{original_layer_names}\n\n"
                f"Final Output Order:\n{final_order}\n\n"
                "Missing layers were automatically created."
            )

            choice = show_custom_dialog("Layer Structure Notice", message)

            if choice == "skip":
                continue
            elif choice == "stop":
                print("Execution stopped by user.")
                return

        # ---------- Save ----------

        xml_dict["Annotations"]["Annotation"] = reordered_layers

        new_xml_path = os.path.join(output_folder, filename)

        with open(new_xml_path, 'w', encoding='utf-8') as file:
            file.write(xmltodict.unparse(xml_dict, pretty=True))

        print(f"Saved: {new_xml_path}")

    print("\nAll files processed successfully.")


if __name__ == "__main__":

    import tkinter as tk
    from tkinter import filedialog, messagebox

    # --- Default layer structure ---
    layer_names = [
        ['islet', 'islets'],
        ['duct', 'ducts', 'normal duct'],
        ['vasculature', 'blood vessel'],
        ['fat'],
        ['acini', 'acinus'],
        ['ecm', 'stroma'],
        ['whitespace', 'white'],
        ['LG Panin', 'panin'],
        ['noise'],
        ['nerve', 'nerves'],
        ['endo', 'endothelium'],
        ['immune'],
        ['PDAC'],
        ['HG panin'],
        ['PanIN 2.5', 'PanIN2.5']
    ]

    root = tk.Tk()
    root.withdraw()

    messagebox.showinfo(
        "Layer Reordering Tool",
        "Select the folder containing Aperio XML annotation files."
    )

    base_path = filedialog.askdirectory(
        title="Select Folder with XML Files"
    )

    if not base_path:
        messagebox.showwarning("No Folder Selected", "Execution cancelled.")
        exit()

    xml_files = glob.glob(os.path.join(base_path, "*.xml"))

    if not xml_files:
        messagebox.showerror(
            "No XML Files Found",
            "The selected folder does not contain XML files."
        )
        exit()

    reorder_layers(base_path, layer_names, case_sensitive=False)

    messagebox.showinfo(
        "Completed",
        "All XML files have been processed successfully."
    )
