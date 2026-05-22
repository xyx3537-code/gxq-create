from Bio import SeqIO

fasta_file = "data/raw/test_virus.fasta"

for record in SeqIO.parse(fasta_file, "fasta"):

    sequence_id = record.id

    sequence = str(record.seq)

    length = len(sequence)

    gc_count = sequence.count("G") + sequence.count("C")

    gc_content = (gc_count / length) * 100

    print(f"ID: {sequence_id}")
    print(f"Length: {length}")
    print(f"GC Content: {gc_content:.2f}%")
    print("-" * 30)