The purpuse of this program is to import a %(collection)s into an anvi'o database.

The input to this program, a %(collection-txt)s, may either have been generated by another anvi'o pprogram (such as %(anvi-export-collection)s), or may have been generated by the user manually. To import a collection into a database, you can run the following command, 

{{ codestart }}
anvi-import-collection %(collection-txt)s \
                       -p %(profile-db)s \
                       -c %(contigs-db)s \
                       -C COLLECTION_NAME
{{ codestop }}

which would import the collection described in the input file formatted as a %(collection-txt)s into the %(profile-db)s with the name `COLLECTION_NAME`.

If your %(collection-txt)s describes contig names rather than split names, you will likely get an anvi'o error. You can fix that by adding the flag `--contigs-mode` to your command:

{{ codestart }}
anvi-import-collection %(collection-txt)s \
                       -p %(profile-db)s \
                       -c %(contigs-db)s \
                       --contigs-mode \
                       -C COLLECTION_NAME
{{ codestop }}