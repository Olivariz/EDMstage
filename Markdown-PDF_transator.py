import pathlib
import os
import fitz
from concurrent.futures import ThreadPoolExecutor, as_completed

def estrai_testo_con_nuova_riga(md_output):
    print("estraggo gli spazi...")
    #Apri il file .md in modalità lettura
    with open(md_output, "r", encoding="utf-8") as file:
        content = file.read()

    #Rimuovi tutti gli spazi doppi
    modified_content = content.replace("  ", " ")

    #Continua a rimuovere gli spazi doppi fino a che non ci sono più
    while "  " in modified_content:
        modified_content = modified_content.replace("  ", " ")

    #Sovrascrivi il file .md originale
    with open(md_output, "w", encoding="utf-8") as file:
        file.write(modified_content)

    print("Gli spazi doppi sono stati rimossi con successo.")
    return md_output
              

def toLowercase(parole_non_modificabili, md_path): 
    print("trasformo caratteri in minuscolo...")
    contenuto_file = ""
    risultato = []
    parola = []
    try:
        # Apertura e lettura del contenuto del file
        with open(md_path, 'r', encoding='utf-8') as file:
            contenuto_file = file.read()

        # Iterazione sui caratteri del contenuto del file
        for carattere in contenuto_file:
            if carattere.isalnum() or carattere == "'":
                parola.append(carattere)
            else:
                if parola:
                    parola_unita = ''.join(parola)
                    if parola_unita.lower() in parole_non_modificabili:
                        risultato.append(parola_unita.upper())
                    else:
                        risultato.append(parola_unita.lower())
                    parola = []
                risultato.append(carattere)

        if parola:
            parola_unita = ''.join(parola)
            if parola_unita in parole_non_modificabili:
                risultato.append(parola_unita.upper())
            else:
                risultato.append(parola_unita.lower())

        # Converti la lista in una stringa per visualizzare il testo modificato
        testo_modificato = ''.join(risultato)
        
    except FileNotFoundError:
        print(f"Errore: il file '{file}' non è stato trovato.")
    except Exception as e:
        print(f"Errore durante la lettura del file: {e}")

    with open(md_path, "w", encoding="utf-8") as file:
        file.write(testo_modificato)
    print("Ho finito di trasformare")
    return md_path                    

def extract_text_with_formatting(page):
    """ Extract text with formatting from a PDF page and convert to Markdown. """
    blocks = page.get_text("dict")["blocks"]
    md_text = ""
    
    for block in blocks:
        if block['type'] == 0:  # this block contains text
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    font = span["font"]
                    size = span["size"]
                    
                    # Example logic for bold and headings
                    if "Bold" in font and text != " " and text != "\n" and text != "":
                        text = f"**{text}** "
                    if size > 20:  # Assume size > 15 as a heading
                        text = f"# {text}"

                    md_text += text
                md_text += "\n"
        md_text += "\n"
    
    return md_text

def pdf_to_markdown(path_to_pdf, md_output):
    try:
        # Apri il documento PDF
        pdf_document = fitz.open(path_to_pdf)
    except FileNotFoundError:
        print("File not found, retry")
        return
    
    md_text = ""
    
    # Itera attraverso tutte le pagine del PDF
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        md_text += extract_text_with_formatting(page).strip("\n")
        md_text = rf"{md_text}"
        if "Tipo Documento" in md_text:
            if "Descrizione Revisione" in md_text:
                da_eliminare=md_text[md_text.find("Tipo Documento"):md_text.find("Descrizione Revisione")+21]
                md_text=md_text.replace(da_eliminare, "")
    
    # Verifica se l'output ha l'estensione .md
    if not md_output.endswith(".md"):
        md_output += ".md"
    
    try:
        # Scrivi il contenuto Markdown su un file
        pathlib.Path(md_output).write_text(md_text, encoding="utf-8")
    except FileExistsError:
        decision = input("File with this name already exists, do you want to overwrite? Y or N ")
        if decision == 'Y':
            pathlib.Path(md_output).write_text(md_text, encoding="utf-8")
        else:
            print("Canceled")
            return
    
    print(f"File created successfully at: {md_output}")
    return md_output

def extract_image(page_index, img_index, img, pdfDocument, imageOutputPath): #funzione per estrarre immagini
    xref = img[0]                                   #inizializza vettore immagini
    base_image = pdfDocument.extract_image(xref)    #...e estrai l'immagine dal documento
    image_bytes = base_image["image"]               #trasforma immagine in una sequenza di byte
    image_ext = base_image["ext"]                   #...e scrivi la sua estensione
    image_output_path = os.path.join(imageOutputPath, f"pagina{page_index+1}immagine{img_index+1}.{image_ext}")#salva il suo path

    with open(image_output_path, "wb") as img_file: #apri buffered writer
        img_file.write(image_bytes)                 #...e scrivi tutte le immagini

    return image_output_path                        #ritorna il path

def extractImages(pathToPDF, images_output_dir):    #la funzione che apre il documento e utilizzando i thread e la funzione extract_image                                              
    try:                                            #estrae immagini e le salva nella directory specificata
        pdfDocument = fitz.open(pathToPDF)          #apre documento
        tasks = []                                  #inizializza la lista "tasks"
    except FileNotFoundError:                       #eccezione
        print("File not found, retry")

    with ThreadPoolExecutor() as executor:          #inizializza il thread
        for page_index in range(len(pdfDocument)):
            pagina = pdfDocument.load_page(page_index)#estrai pagine
            immagini = pagina.get_images(full=True) #estrai immagini dalla pagina
            
            for img_index, img in enumerate(immagini):
                tasks.append(executor.submit(extract_image, page_index, img_index, img, pdfDocument, images_output_dir))#inizializza la task che estrae immagine
        
        for future in as_completed(tasks):          #quando completato...
            try:                                    
                result = future.result()            #ottieni risultato
                print(f"Image saved: {result}")     #stampa risultato
            except Exception as e:                  #se no...
                print(f"An error occurred: {e}")    #stampa errore

    print("Files created successfully in the following dir: " + images_output_dir)


if __name__ == "__main__":
    #Funzione per passare gli input alla funzione "pdf_to_markdown_with_images"
    def PDF_To_MD():                                #funzione che unisce tutte le funzioni precedenti, chiede input all'utente e fa partire i thread
            
            # Inserisci il percorso del PDF
            path_to_pdf = input("Inserisci il percorso del PDF: ")

             # Inserisci il nome del file del Markdown
            name = os.path.join(os.path.expanduser('~'), "Documents")
            name = os.path.join(name, "EDM")
            name1= os.path.splitext(os.path.basename(path_to_pdf))[0]
            md_output =os.path.join(name ,name1)


            # Inserisci il nome della directory per le immagini estratte
            path = os.path.join(os.path.expanduser('~'), "Pictures")
            path = os.path.join(path, "EDM")

            images_output_dir = os.path.join(path, name1)

            os.makedirs(images_output_dir, exist_ok=True)

            tasks=[]
            with ThreadPoolExecutor() as executor:
                tasks.append(executor.submit(extractImages, path_to_pdf, images_output_dir))

                for future in as_completed(tasks):
                    try:
                        result = future.result()
                        print(f"File saved: {result}")
                    except Exception as e:
                        print(f"An error occurred: {e}")
            parole_non_modificabili={ }
            parole=input("scrivi parole separate della virgola: ").split(",")
            for parola in parole:
                parole_non_modificabili[parola]= None
            md_output=pdf_to_markdown(path_to_pdf, md_output)
            md_output=estrai_testo_con_nuova_riga(md_output)
            toLowercase(parole_non_modificabili,md_output)

            
             # Esegui la conversione e l'estrazione delle immagini
            
           


#Funzione per il menu con match case
    def menu(scelta):
        match scelta:
            case 0:
                exit()
            case 1:
                PDF_To_MD()
                scelta = 100
                


    def main():
        scelta = 100
        while(scelta != 0):
            print("Benvenuto! cosa si vuole fare? \n 0. Uscire \n 1. Convertire un file PDF in Markdown \n")
            scelta = input("Inserire il numero per svolgere l'opzione desiderata: ")
            scelta = int(scelta)
            menu(scelta)


    main()
