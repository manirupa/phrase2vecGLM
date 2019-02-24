## Phrase2VecGLM

#### A neural phrasal embedding-based generalized language model for semantic tagging for complex query reformulation. 

#### Details about the model can be found in this paper: http://www.aclweb.org/anthology/W18-2313

### Overall Process: _(still in progress..)_

Step 0: Set up ElasticSearch (ES) index (needed for evaluation of GLM) on PMC article dataset provided here: http://www.trec-cds.org/2016.html\#documents

Run the following steps in the specified order, for:
a) corpus processing to generate document and collection-level statistics, 
b) model building and inference (semantic tagging of queries or query documents) and 
c) evaluation via query preparation for and run on ES 

_a) Corpus processing for document/collection statistics_ (Order is important.):

0) Run make_phrases.py --- (Phrase-tokenize input text file and regenerate phrase-based input first, to learn phrasal word2vec next)
1) Run PMCword2vec-model.py --- (Obtain model; make vocab.txt in model folder by cut command to get first column of text-based model file)
usage: `./PMCword2vec-model.py <input_text_file> <experimental_setting_list format_file> <description_text>`
2) Run PMCtfidf-model.py  --- (Needs vocab.txt from previous step. Generates indexed_vocab.txt.)
usage: `./PMCtfidf-model.py <prefix> (model folder) <input_text_file> <vocabfile> (full path to vocab.txt) <description_text (for unique run)> <topN>`
3) Run PMCsimttp-model.py --- (Needs indexed_vocab.txt from previous step)
usage: `./PMCsimttp-model.py <prefix> (just model folder name) <documents_file_full_path> <description_text (for unique run)>`

_b) Prepare for model building and inference_

4) Run make_queries.py --- (make the queries, generate queries for query docs from doc ids to generate concepts for those docs)
usage: `make_queries.py <input_docid_file (one id per line)> <model_topntfidf_file> <output_query_file>`

5) Run documents_genscores_GLM_test.py  ---  (reads indexed_vocab.txt, uses queries from models/queries/<query_doc_file>)
usage: `usage: ./documents_genscores_GLM_test.py <prefix> (just model folder name) <phrvecmodel+sim_run_prefix> <run_description (LM)> <LM parameters file e.g. 3ql> <doc id list file (one per line) [obsolete]> <query_file> <query_length (upto 5)>`
(5) Run documents_generate_concepts.py  ---  (reads indexed_vocab.txt --- optional to generate concepts from post-processing)
usage: `usage: ./documents_generate_concepts.py <prefix (just model folder name)> <prev_run_prefix> <concept / document score_file_name> <run_desc (unique)>`

_c) Evaluation via query preparation for and run on ES for Feedback Loop QE setting_

6) Run ./generate_QEs_phrases.py 
usage: `./generate_QEs_phrases.py <pipe_sep_input_IDs_file> <methods_setting_file> <folder_prefix_full_path> <num_concepts>`
e.g.: `./generate_QEs_phrases.py goodinput/IDs/2ndPhase_RankedArticles-NoneBM25Top15IDsPipeSep.txt goodinput/methods_settings/methods_settings_phrases437_interpolated_model_params_uA0.3pB0.4.txt models/model_w2v_vs50_cw4_run_phrases_docs_phrase-embedded_l2-3_use 3`

7) Make query file for Search Engine (ES) run  by joining 2 files:
e.g.: `paste goodinput/SEqueries/generated/queries_2ndlevel.txt goodinput/SEqueries/methods_QEterms_methods_settings_phrases437_interpolated_model_params_uA0.3pB0.4.txt > goodinput/SEqueries/queries_phrases437_interpolated_model_params_uA0.3pB0.4.txt`

8) Run the makeRunSEfile.py to generate code blocks to paste into Search.js for Search Engine (ES) runs and generate rankings.

9) Finally run runevals.py on the set of `RankedArticles` files generated from above SE runs into some output folder e.g. `2ndPhaseOutput`
 E.g. usage 1: `./runevals.py <folder_full_path> (containing RankedArticles output files e.g. /Users/<user1>/Documents/Phrase2VecGLM/2ndPhaseOutput/Run-IPV2-1-10)`
 E.g. usage 2: `./runevals.py ../2ndPhaseOutput/PhrasalAddlBaselines/`

_d) Evaluation via query preparation for and run on ES for Direct QE setting_ (coming soon..)
