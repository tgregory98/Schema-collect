from SPARQLWrapper import SPARQLWrapper
import modules.tr_funcs


class SchemaBuilder:
    def __init__(self, filter_set_edges=[], filter_set_vertices=[]):
        self.name = "SchemaBuilder"
        self.filter_set_edges = filter_set_edges
        self.filter_set_vertices = filter_set_vertices

    def filter_query_pred_gen(self):
        filter_query_pred = ""
        for i in range(len(self.filter_set_edges)):
            if len(self.filter_set_edges) == 0:
                break
            elif len(self.filter_set_edges) == 1:
                string = "FILTER(regex(?pred&, &&))"
                filter_query_pred = string.replace("&&", str(self.filter_set_edges[0]))
            elif i == 0:
                filter_query_pred = "FILTER("
                string = "regex(?pred&, &&)"
                filter_query_pred = filter_query_pred + string.replace("&&", str(self.filter_set_edges[i]))
            elif i < len(self.filter_set_edges) - 1:
                string = "||regex(?pred&, &&)"
                filter_query_pred = filter_query_pred + string.replace("&&", str(self.filter_set_edges[i]))
            elif i == len(self.filter_set_edges) - 1:
                string = "||regex(?pred&, &&))"
                filter_query_pred = filter_query_pred + string.replace("&&", str(self.filter_set_edges[i]))

        return filter_query_pred

    def filter_query_pred_inv_gen(self):
        filter_query_pred_inv = ""
        for i in range(len(self.filter_set_edges)):
            if len(self.filter_set_edges) == 0:
                break
            elif len(self.filter_set_edges) == 1:
                string = "FILTER(regex(?pred_inv&, &&))"
                filter_query_pred_inv = string.replace("&&", str(self.filter_set_edges[0]))
            elif i == 0:
                filter_query_pred_inv = "FILTER("
                string = "regex(?pred_inv&, &&)"
                filter_query_pred_inv = filter_query_pred_inv + string.replace("&&", str(self.filter_set_edges[i]))
            elif i < len(self.filter_set_edges) - 1:
                string = "||regex(?pred_inv&, &&)"
                filter_query_pred_inv = filter_query_pred_inv + string.replace("&&", str(self.filter_set_edges[i]))
            elif i == len(self.filter_set_edges) - 1:
                string = "||regex(?pred_inv&, &&))"
                filter_query_pred_inv = filter_query_pred_inv + string.replace("&&", str(self.filter_set_edges[i]))
        
        return filter_query_pred_inv

    def filter_query_vertex_gen(self):
        filter_query_vertex = ""
        for i in range(len(self.filter_set_vertices)):
            if len(self.filter_set_vertices) == 0:
                break
            elif len(self.filter_set_vertices) == 1:
                string = "FILTER(regex(?n&, &&))"
                filter_query_vertex = string.replace("&&", str(self.filter_set_vertices[0]))
            elif i == 0:
                filter_query_vertex = "FILTER("
                string = "regex(?n&, &&)"
                filter_query_vertex = filter_query_vertex + string.replace("&&", str(self.filter_set_vertices[i]))
            elif i < len(self.filter_set_vertices) - 1:
                string = "||regex(?n&, &&)"
                filter_query_vertex = filter_query_vertex + string.replace("&&", str(self.filter_set_vertices[i]))
            elif i == len(self.filter_set_vertices) - 1:
                string = "||regex(?n&, &&))"
                filter_query_vertex = filter_query_vertex + string.replace("&&", str(self.filter_set_vertices[i]))
        
        return filter_query_vertex

    def cypher_url_gen(self, sparql_query):
        wrapper = SPARQLWrapper("http://dbpedia.org/sparql")
        wrapper.setQuery(sparql_query)
        wrapper.setReturnFormat("csv")
        query_result = wrapper.query()
        url = query_result.geturl()

        return url

    def run(self, depth):
        sparql_query = self.sparql_query_gen(depth)
        url = self.cypher_url_gen(sparql_query)
        cypher_query = self.cypher_query_gen(depth, url)
        modules.tr_funcs.commit_cypher_query(cypher_query)


class PairwiseSchemaBuilder(SchemaBuilder):
    def __init__(self, start_page, end_page, filter_set_edges=[], filter_set_vertices=[]):
        self.name = "PairwiseSchemaBuilder between " + start_page + " and " + end_page
        self.start_page = start_page
        self.end_page = end_page
        self.filter_set_edges = filter_set_edges
        self.filter_set_vertices = filter_set_vertices

    def sparql_query_gen(self, depth):
        query_part1 = "\rSELECT "
        for i in range(depth - 1):
            string = "?pred& ?pred_inv& ?n& "
            query_part1 = query_part1 + string.replace("&", str(i + 1))
        final_string = "?pred& ?pred_inv&\r"
        query_part1 = query_part1 + final_string.replace("&", str(depth))

        filter_query_pred = self.filter_query_pred_gen()
        filter_query_pred_inv = self.filter_query_pred_inv_gen()
        filter_query_vertex = self.filter_query_vertex_gen()
        filter_query_vertex_mid = filter_query_vertex + filter_query_vertex.replace("&", "&&")
        filter_query_vertex_mid = filter_query_vertex_mid.replace(")FILTER(", "||")

        query_part2_open = """
    WHERE {
        """

        query_part2_a = """
        { {
            <""" + self.start_page + """> ?pred1 ?n1
        } UNION {
            ?n1 ?pred_inv1 <""" + self.start_page + """>
        } } .
        """
        query_part2_b = """
        { {
            """ + filter_query_pred.replace("&", "1") + """
            <""" + self.start_page + """> ?pred1 ?n1
        } UNION {
            """ + filter_query_pred_inv.replace("&", "1") + """
            ?n1 ?pred_inv1 <""" + self.start_page + """>
        } } .
        """
        query_part2_c = """
        { {
            """ + filter_query_vertex.replace("&", "1") + """
            <""" + self.start_page + """> ?pred1 ?n1
        } UNION {
            """ + filter_query_vertex.replace("&", "1") + """
            ?n1 ?pred_inv1 <""" + self.start_page + """>
        } } .
        """
        for i in range(depth - 2):
            block_a = """
        { {
            ?n& ?pred&& ?n&&
        } UNION {
            ?n&& ?pred_inv&& ?n&
        } } .
            """
            block_b = """
        { {
            """ + filter_query_pred.replace("&", str(i + 2)) + """
            ?n& ?pred&& ?n&&
        } UNION {
            """ + filter_query_pred_inv.replace("&", str(i + 2)) + """
            ?n&& ?pred_inv&& ?n&
        } } .
            """
            block_c = """
        { {
            """ + filter_query_vertex_mid + """
            ?n& ?pred&& ?n&&
        } UNION {
            """ + filter_query_vertex_mid + """
            ?n&& ?pred_inv&& ?n&
        } } .
            """
            query_part2_a = query_part2_a + block_a.replace("&&", str(i + 2)).replace("&", str(i + 1))
            query_part2_b = query_part2_b + block_b.replace("&&", str(i + 2)).replace("&", str(i + 1))
            query_part2_c = query_part2_c + block_c.replace("&&", str(i + 2)).replace("&", str(i + 1))

        final_block_a = """
        { {
            """ + filter_query_pred.replace("&", str(depth)) + """
            ?n& ?pred&& <""" + self.end_page + """>
        } UNION {
            """ + filter_query_pred_inv.replace("&", str(depth)) + """
            <""" + self.end_page + """> ?pred_inv&& ?n&
        } } .
        """
        final_block_b = """
        { {
            """ + filter_query_pred.replace("&", str(depth)) + """
            ?n& ?pred&& <""" + self.end_page + """>
        } UNION {
            """ + filter_query_pred_inv.replace("&", str(depth)) + """
            <""" + self.end_page + """> ?pred_inv&& ?n&
        } } .
        """
        final_block_c = """
        { {
            """ + filter_query_vertex + """
            ?n& ?pred&& <""" + self.end_page + """>
        } UNION {
            """ + filter_query_vertex + """
            <""" + self.end_page + """> ?pred_inv&& ?n&
        } } .
        """
        query_part2_a = query_part2_a + final_block_a.replace("&&", str(depth)).replace("&", str(depth - 1))
        query_part2_b = query_part2_b + final_block_b.replace("&&", str(depth)).replace("&", str(depth - 1))
        query_part2_c = query_part2_c + final_block_c.replace("&&", str(depth)).replace("&", str(depth - 1))

        query_part2_close = """
    }
        """

        if len(self.filter_set_edges) == 0 and len(self.filter_set_vertices) == 0:
            query_part2 = query_part2_open + query_part2_a + query_part2_close
        elif len(self.filter_set_edges) != 0 and len(self.filter_set_vertices) != 0:
            query_part2 = query_part2_open + query_part2_b + query_part2_c + query_part2_close
        elif len(self.filter_set_vertices) == 0:
            query_part2 = query_part2_open + query_part2_b + query_part2_close
        elif len(self.filter_set_edges) == 0:
            query_part2 = query_part2_open + query_part2_c + query_part2_close

        query = query_part1 + query_part2

        return query

    def cypher_query_gen(self, depth, url):
        query_part1 = "WITH \"" + url + "\" AS url\r\rLOAD CSV WITH HEADERS FROM url AS row\r\r"

        query_part2 = "MERGE (n0:root_node:page {iri: \"" + self.start_page + "\"})\r"
        for i in range(depth - 1):
            string = "MERGE (n&:nonroot_node:page {iri: row.n&})\r"
            query_part2 = query_part2 + string.replace("&", str(i + 1))
        final_string = "MERGE (n&:root_node:page {iri: \"" + self.end_page + "\"})\r"
        query_part2 = query_part2 + final_string.replace("&", str(depth))

        query_part3 = ""
        for i in range(depth):
            block = """
    FOREACH (x IN CASE WHEN row.pred&& IS NULL THEN [] ELSE [1] END | MERGE (n&)-[p:pred {iri: row.pred&&}]->(n&&))
    FOREACH (x IN CASE WHEN row.pred_inv&& IS NULL THEN [] ELSE [1] END | MERGE (n&)<-[p:pred {iri: row.pred_inv&&}]-(n&&))
            """
            query_part3 = query_part3 + block.replace("&&", str(i + 1)).replace("&", str(i))

        query_part4 = "\rRETURN "
        for i in range(depth):
            string = "n&, "
            query_part4 = query_part4 + string.replace("&", str(i))
        final_string = "n&"
        query_part4 = query_part4 + final_string.replace("&", str(depth))

        query = query_part1 + query_part2 + query_part3 + query_part4

        return query


class ParentSchemaBuilder(SchemaBuilder):
    def __init__(self, page, filter_set_edges=[], filter_set_vertices=[]):
        self.name = "ParentSchemaBuilder on " + page
        self.page = page
        self.filter_set_edges = filter_set_edges
        self.filter_set_vertices = filter_set_vertices

    def sparql_query_gen(self, depth):
        query_part1 = "\rSELECT "
        for i in range(depth):
            string = "?pred& ?n& "
            query_part1 = query_part1 + string.replace("&", str(i + 1))

        filter_query_pred = self.filter_query_pred_gen()
        filter_query_vertex = self.filter_query_vertex_gen()
        filter_query_vertex_mid = filter_query_vertex + filter_query_vertex.replace("&", "&&")
        filter_query_vertex_mid = filter_query_vertex_mid.replace(")FILTER(", "||")

        query_part2_open = """
    WHERE {
        """

        query_part2_a = """
        {
            <""" + self.page + """> ?pred1 ?n1
        } .
        """
        query_part2_b = """
        {
            """ + filter_query_pred.replace("&", "1") + """
            <""" + self.page + """> ?pred1 ?n1
        } .
        """
        query_part2_c = """
        {
            """ + filter_query_vertex.replace("&", "1") + """
            <""" + self.page + """> ?pred1 ?n1
        } .
        """
        for i in range(depth - 1):
            block_a = """
        {
            ?n& ?pred&& ?n&&
        } .
            """
            block_b = """
        {
            """ + filter_query_pred.replace("&", "&&") + """
            ?n& ?pred&& ?n&&
        } .
            """
            block_c = """
        {
            """ + filter_query_vertex_mid + """
            ?n& ?pred&& ?n&&
        } .
            """
            query_part2_a = query_part2_a + block_a.replace("&&", str(i + 2)).replace("&", str(i + 1))
            query_part2_b = query_part2_b + block_b.replace("&&", str(i + 2)).replace("&", str(i + 1))
            query_part2_c = query_part2_c + block_c.replace("&&", str(i + 2)).replace("&", str(i + 1))

        query_part2_close = """
    }
        """

        if len(self.filter_set_edges) == 0 and len(self.filter_set_vertices) == 0:
            query_part2 = query_part2_open + query_part2_a + query_part2_close
        elif len(self.filter_set_edges) != 0 and len(self.filter_set_vertices) != 0:
            query_part2 = query_part2_open + query_part2_b + query_part2_c + query_part2_close
        elif len(self.filter_set_vertices) == 0:
            query_part2 = query_part2_open + query_part2_b + query_part2_close
        elif len(self.filter_set_edges) == 0:
            query_part2 = query_part2_open + query_part2_c + query_part2_close

        query = query_part1 + query_part2

        return query

    def cypher_query_gen(self, depth, url):
        query_part1 = "WITH \"" + url + "\" AS url\r\rLOAD CSV WITH HEADERS FROM url AS row\r\r"

        query_part2 = "MERGE (n0:root_node:page {iri: \"" + self.page + "\"})\r"
        for i in range(depth):
            string = "MERGE (n&:nonroot_node:page {iri: row.n&})\r"
            query_part2 = query_part2 + string.replace("&", str(i + 1))

        query_part3 = ""
        for i in range(depth):
            block = """
    FOREACH (x IN CASE WHEN row.pred&& IS NULL THEN [] ELSE [1] END | MERGE (n&)-[p:pred {iri: row.pred&&}]->(n&&))
            """
            query_part3 = query_part3 + block.replace("&&", str(i + 1)).replace("&", str(i))

        query_part4 = "\rRETURN "
        for i in range(depth):
            string = "n&, "
            query_part4 = query_part4 + string.replace("&", str(i))
        final_string = "n&"
        query_part4 = query_part4 + final_string.replace("&", str(depth))

        query = query_part1 + query_part2 + query_part3 + query_part4

        return query


class PopulateSchemaBuilder(SchemaBuilder):
    def __init__(self, page, filter_set_edges=[], filter_set_vertices=[]):
        self.name = "PopulateSchemaBuilder on " + page
        self.page = page
        self.filter_set_edges = filter_set_edges
        self.filter_set_vertices = filter_set_vertices

    def sparql_query_gen(self, depth):
        query_part1 = "\rSELECT "
        for i in range(depth):
            string = "?pred& ?pred_inv& ?n& "
            query_part1 = query_part1 + string.replace("&", str(i + 1))

        filter_query_pred = self.filter_query_pred_gen()
        filter_query_pred_inv = self.filter_query_pred_inv_gen()
        filter_query_vertex = self.filter_query_vertex_gen()
        filter_query_vertex_mid = filter_query_vertex + filter_query_vertex.replace("&", "&&")
        filter_query_vertex_mid = filter_query_vertex_mid.replace(")FILTER(", "||")

        query_part2_open = """
    WHERE {
        """

        query_part2_a = """
        { {
            <""" + self.page + """> ?pred1 ?n1
        } UNION {
            ?n1 ?pred_inv1 <""" + self.page + """>
        } } .
        """
        query_part2_b = """
        { {
            """ + filter_query_pred.replace("&", "1") + """
            <""" + self.page + """> ?pred1 ?n1
        } UNION {
            """ + filter_query_pred_inv.replace("&", "1") + """
            ?n1 ?pred_inv1 <""" + self.page + """>
        } } .
        """
        query_part2_c = """
        { {
            """ + filter_query_vertex.replace("&", "1") + """
            <""" + self.page + """> ?pred1 ?n1
        } UNION {
            """ + filter_query_vertex.replace("&", "1") + """
            ?n1 ?pred_inv1 <""" + self.page + """>
        } } .
        """
        for i in range(depth - 1):
            block_a = """
        { {
            ?n& ?pred&& ?n&&
        } UNION {
            ?n&& ?pred_inv&& ?n&
        } } .
            """
            block_b = """
        { {
            """ + filter_query_pred.replace("&", str(i + 2)) + """
            ?n& ?pred&& ?n&&
        } UNION {
            """ + filter_query_pred_inv.replace("&", str(i + 2)) + """
            ?n&& ?pred_inv&& ?n&
        } } .
            """
            block_c = """
        { {
            """ + filter_query_vertex_mid + """
            ?n& ?pred&& ?n&&
        } UNION {
            """ + filter_query_vertex_mid + """
            ?n&& ?pred_inv&& ?n&
        } } .
            """
            query_part2_a = query_part2_a + block_a.replace("&&", str(i + 2)).replace("&", str(i + 1))
            query_part2_b = query_part2_b + block_b.replace("&&", str(i + 2)).replace("&", str(i + 1))
            query_part2_c = query_part2_c + block_c.replace("&&", str(i + 2)).replace("&", str(i + 1))

        query_part2_close = """
    }
        """

        if len(self.filter_set_edges) == 0 and len(self.filter_set_vertices) == 0:
            query_part2 = query_part2_open + query_part2_a + query_part2_close
        elif len(self.filter_set_edges) != 0 and len(self.filter_set_vertices) != 0:
            query_part2 = query_part2_open + query_part2_b + query_part2_c + query_part2_close
        elif len(self.filter_set_vertices) == 0:
            query_part2 = query_part2_open + query_part2_b + query_part2_close
        elif len(self.filter_set_edges) == 0:
            query_part2 = query_part2_open + query_part2_c + query_part2_close

        query = query_part1 + query_part2

        return query

    def cypher_query_gen(self, depth, url):
        query_part1 = "WITH \"" + url + "\" AS url\r\rLOAD CSV WITH HEADERS FROM url AS row\r\r"

        query_part2 = "MERGE (n0:root_node:page {iri: \"" + self.page + "\"})\r"
        for i in range(depth):
            string = "MERGE (n&:nonroot_node:page {iri: row.n&})\r"
            query_part2 = query_part2 + string.replace("&", str(i + 1))

        query_part3 = ""
        for i in range(depth):
            block = """
    FOREACH (x IN CASE WHEN row.pred&& IS NULL THEN [] ELSE [1] END | MERGE (n&)-[p:pred {iri: row.pred&&}]->(n&&))
    FOREACH (x IN CASE WHEN row.pred_inv&& IS NULL THEN [] ELSE [1] END | MERGE (n&)<-[p:pred {iri: row.pred_inv&&}]-(n&&))
            """
            query_part3 = query_part3 + block.replace("&&", str(i + 1)).replace("&", str(i))

        query_part4 = "\rRETURN "
        for i in range(depth):
            string = "n&, "
            query_part4 = query_part4 + string.replace("&", str(i))
        final_string = "n&"
        query_part4 = query_part4 + final_string.replace("&", str(depth))

        query = query_part1 + query_part2 + query_part3 + query_part4

        return query