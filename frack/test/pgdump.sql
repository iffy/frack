--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: attachment; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE attachment (
    type text NOT NULL,
    id text NOT NULL,
    filename text NOT NULL,
    size integer,
    "time" integer,
    description text,
    author text,
    ipnr text
);


ALTER TABLE public.attachment OWNER TO "trac-migration";

--
-- Name: auth_cookie; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE auth_cookie (
    cookie text NOT NULL,
    name text NOT NULL,
    ipnr text NOT NULL,
    "time" integer
);


ALTER TABLE public.auth_cookie OWNER TO "trac-migration";

--
-- Name: component; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE component (
    name text NOT NULL,
    owner text,
    description text
);


ALTER TABLE public.component OWNER TO "trac-migration";

--
-- Name: component_default_cc; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE component_default_cc (
    name text NOT NULL,
    cc text
);


ALTER TABLE public.component_default_cc OWNER TO "trac-migration";

--
-- Name: enum; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE enum (
    type text NOT NULL,
    name text NOT NULL,
    value text
);


ALTER TABLE public.enum OWNER TO "trac-migration";

--
-- Name: milestone; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE milestone (
    name text NOT NULL,
    due integer,
    completed integer,
    description text
);


ALTER TABLE public.milestone OWNER TO "trac-migration";

--
-- Name: node_change; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE node_change (
    rev text NOT NULL,
    path text NOT NULL,
    node_type text,
    change_type text NOT NULL,
    base_path text,
    base_rev text
);


ALTER TABLE public.node_change OWNER TO "trac-migration";

--
-- Name: permission; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE permission (
    username text NOT NULL,
    action text NOT NULL
);


ALTER TABLE public.permission OWNER TO "trac-migration";

--
-- Name: report; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE report (
    id integer NOT NULL,
    author text,
    title text,
    query text,
    description text
);


ALTER TABLE public.report OWNER TO "trac-migration";

--
-- Name: report_id_seq; Type: SEQUENCE; Schema: public; Owner: trac-migration
--

CREATE SEQUENCE report_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.report_id_seq OWNER TO "trac-migration";

--
-- Name: report_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trac-migration
--

ALTER SEQUENCE report_id_seq OWNED BY report.id;


--
-- Name: revision; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE revision (
    rev text NOT NULL,
    "time" integer,
    author text,
    message text
);


ALTER TABLE public.revision OWNER TO "trac-migration";

--
-- Name: session; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE session (
    sid text NOT NULL,
    authenticated integer NOT NULL,
    last_visit integer
);


ALTER TABLE public.session OWNER TO "trac-migration";

--
-- Name: session_attribute; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE session_attribute (
    sid text NOT NULL,
    authenticated integer NOT NULL,
    name text NOT NULL,
    value text
);


ALTER TABLE public.session_attribute OWNER TO "trac-migration";

--
-- Name: spamfilter_bayes; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE spamfilter_bayes (
    word text NOT NULL,
    nspam integer,
    nham integer
);


ALTER TABLE public.spamfilter_bayes OWNER TO "trac-migration";

--
-- Name: spamfilter_log; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE spamfilter_log (
    id integer NOT NULL,
    "time" integer,
    path text,
    author text,
    authenticated integer,
    ipnr text,
    headers text,
    content text,
    rejected integer,
    karma integer,
    reasons text
);


ALTER TABLE public.spamfilter_log OWNER TO "trac-migration";

--
-- Name: spamfilter_log_id_seq; Type: SEQUENCE; Schema: public; Owner: trac-migration
--

CREATE SEQUENCE spamfilter_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.spamfilter_log_id_seq OWNER TO "trac-migration";

--
-- Name: spamfilter_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trac-migration
--

ALTER SEQUENCE spamfilter_log_id_seq OWNED BY spamfilter_log.id;


--
-- Name: system; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE system (
    name text NOT NULL,
    value text
);


ALTER TABLE public.system OWNER TO "trac-migration";

--
-- Name: ticket; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE ticket (
    id integer NOT NULL,
    type text,
    "time" integer,
    changetime integer,
    component text,
    severity text,
    priority text,
    owner text,
    reporter text,
    cc text,
    version text,
    milestone text,
    status text,
    resolution text,
    summary text,
    description text,
    keywords text
);


ALTER TABLE public.ticket OWNER TO "trac-migration";

--
-- Name: ticket_change; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE ticket_change (
    ticket integer NOT NULL,
    "time" integer NOT NULL,
    author text,
    field text NOT NULL,
    oldvalue text,
    newvalue text
);


ALTER TABLE public.ticket_change OWNER TO "trac-migration";

--
-- Name: ticket_custom; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE ticket_custom (
    ticket integer NOT NULL,
    name text NOT NULL,
    value text
);


ALTER TABLE public.ticket_custom OWNER TO "trac-migration";

--
-- Name: ticket_id_seq; Type: SEQUENCE; Schema: public; Owner: trac-migration
--

CREATE SEQUENCE ticket_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ticket_id_seq OWNER TO "trac-migration";

--
-- Name: ticket_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trac-migration
--

ALTER SEQUENCE ticket_id_seq OWNED BY ticket.id;


--
-- Name: version; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE version (
    name text NOT NULL,
    "time" integer,
    description text
);


ALTER TABLE public.version OWNER TO "trac-migration";

--
-- Name: wiki; Type: TABLE; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE TABLE wiki (
    name text NOT NULL,
    version integer NOT NULL,
    "time" integer,
    author text,
    ipnr text,
    text text,
    comment text,
    readonly integer
);


ALTER TABLE public.wiki OWNER TO "trac-migration";

--
-- Name: id; Type: DEFAULT; Schema: public; Owner: trac-migration
--

ALTER TABLE report ALTER COLUMN id SET DEFAULT nextval('report_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: trac-migration
--

ALTER TABLE spamfilter_log ALTER COLUMN id SET DEFAULT nextval('spamfilter_log_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: trac-migration
--

ALTER TABLE ticket ALTER COLUMN id SET DEFAULT nextval('ticket_id_seq'::regclass);


--
-- Name: attachment_pk; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY attachment
    ADD CONSTRAINT attachment_pk PRIMARY KEY (type, id, filename);


--
-- Name: auth_cookie_pk; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY auth_cookie
    ADD CONSTRAINT auth_cookie_pk PRIMARY KEY (cookie, ipnr, name);


--
-- Name: component_default_cc_pkey; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY component_default_cc
    ADD CONSTRAINT component_default_cc_pkey PRIMARY KEY (name);


--
-- Name: component_pkey; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY component
    ADD CONSTRAINT component_pkey PRIMARY KEY (name);


--
-- Name: enum_pk; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY enum
    ADD CONSTRAINT enum_pk PRIMARY KEY (type, name);


--
-- Name: milestone_pkey; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY milestone
    ADD CONSTRAINT milestone_pkey PRIMARY KEY (name);


--
-- Name: node_change_pk; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY node_change
    ADD CONSTRAINT node_change_pk PRIMARY KEY (rev, path, change_type);


--
-- Name: permission_pk; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY permission
    ADD CONSTRAINT permission_pk PRIMARY KEY (username, action);


--
-- Name: report_pkey; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY report
    ADD CONSTRAINT report_pkey PRIMARY KEY (id);


--
-- Name: revision_pkey; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY revision
    ADD CONSTRAINT revision_pkey PRIMARY KEY (rev);


--
-- Name: session_attribute_pk; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY session_attribute
    ADD CONSTRAINT session_attribute_pk PRIMARY KEY (sid, authenticated, name);


--
-- Name: session_pk; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY session
    ADD CONSTRAINT session_pk PRIMARY KEY (sid, authenticated);


--
-- Name: spamfilter_bayes_pkey; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY spamfilter_bayes
    ADD CONSTRAINT spamfilter_bayes_pkey PRIMARY KEY (word);


--
-- Name: spamfilter_log_pkey; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY spamfilter_log
    ADD CONSTRAINT spamfilter_log_pkey PRIMARY KEY (id);


--
-- Name: system_pkey; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY system
    ADD CONSTRAINT system_pkey PRIMARY KEY (name);


--
-- Name: ticket_change_pk; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY ticket_change
    ADD CONSTRAINT ticket_change_pk PRIMARY KEY (ticket, "time", field);


--
-- Name: ticket_custom_pk; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY ticket_custom
    ADD CONSTRAINT ticket_custom_pk PRIMARY KEY (ticket, name);


--
-- Name: ticket_pkey; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY ticket
    ADD CONSTRAINT ticket_pkey PRIMARY KEY (id);


--
-- Name: version_pkey; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY version
    ADD CONSTRAINT version_pkey PRIMARY KEY (name);


--
-- Name: wiki_pk; Type: CONSTRAINT; Schema: public; Owner: trac-migration; Tablespace: 
--

ALTER TABLE ONLY wiki
    ADD CONSTRAINT wiki_pk PRIMARY KEY (name, version);


--
-- Name: component_default_cc_name_idx; Type: INDEX; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE INDEX component_default_cc_name_idx ON component_default_cc USING btree (name);


--
-- Name: node_change_rev_idx; Type: INDEX; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE INDEX node_change_rev_idx ON node_change USING btree (rev);


--
-- Name: revision_time_idx; Type: INDEX; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE INDEX revision_time_idx ON revision USING btree ("time");


--
-- Name: session_authenticated_idx; Type: INDEX; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE INDEX session_authenticated_idx ON session USING btree (authenticated);


--
-- Name: session_last_visit_idx; Type: INDEX; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE INDEX session_last_visit_idx ON session USING btree (last_visit);


--
-- Name: ticket_change_ticket_idx; Type: INDEX; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE INDEX ticket_change_ticket_idx ON ticket_change USING btree (ticket);


--
-- Name: ticket_change_time_idx; Type: INDEX; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE INDEX ticket_change_time_idx ON ticket_change USING btree ("time");


--
-- Name: ticket_status_idx; Type: INDEX; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE INDEX ticket_status_idx ON ticket USING btree (status);


--
-- Name: ticket_time_idx; Type: INDEX; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE INDEX ticket_time_idx ON ticket USING btree ("time");


--
-- Name: wiki_time_idx; Type: INDEX; Schema: public; Owner: trac-migration; Tablespace: 
--

CREATE INDEX wiki_time_idx ON wiki USING btree ("time");


--
-- Name: public; Type: ACL; Schema: -; Owner: trac-migration
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM "trac-migration";
GRANT ALL ON SCHEMA public TO "trac-migration";
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: attachment; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE attachment FROM PUBLIC;
REVOKE ALL ON TABLE attachment FROM "trac-migration";
GRANT ALL ON TABLE attachment TO "trac-migration";
GRANT SELECT ON TABLE attachment TO washort;


--
-- Name: auth_cookie; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE auth_cookie FROM PUBLIC;
REVOKE ALL ON TABLE auth_cookie FROM "trac-migration";
GRANT ALL ON TABLE auth_cookie TO "trac-migration";
GRANT SELECT ON TABLE auth_cookie TO washort;


--
-- Name: component; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE component FROM PUBLIC;
REVOKE ALL ON TABLE component FROM "trac-migration";
GRANT ALL ON TABLE component TO "trac-migration";
GRANT SELECT ON TABLE component TO washort;


--
-- Name: component_default_cc; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE component_default_cc FROM PUBLIC;
REVOKE ALL ON TABLE component_default_cc FROM "trac-migration";
GRANT ALL ON TABLE component_default_cc TO "trac-migration";
GRANT SELECT ON TABLE component_default_cc TO washort;


--
-- Name: enum; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE enum FROM PUBLIC;
REVOKE ALL ON TABLE enum FROM "trac-migration";
GRANT ALL ON TABLE enum TO "trac-migration";
GRANT SELECT ON TABLE enum TO washort;


--
-- Name: milestone; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE milestone FROM PUBLIC;
REVOKE ALL ON TABLE milestone FROM "trac-migration";
GRANT ALL ON TABLE milestone TO "trac-migration";
GRANT SELECT ON TABLE milestone TO washort;


--
-- Name: node_change; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE node_change FROM PUBLIC;
REVOKE ALL ON TABLE node_change FROM "trac-migration";
GRANT ALL ON TABLE node_change TO "trac-migration";
GRANT SELECT ON TABLE node_change TO washort;


--
-- Name: permission; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE permission FROM PUBLIC;
REVOKE ALL ON TABLE permission FROM "trac-migration";
GRANT ALL ON TABLE permission TO "trac-migration";
GRANT SELECT ON TABLE permission TO washort;


--
-- Name: report; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE report FROM PUBLIC;
REVOKE ALL ON TABLE report FROM "trac-migration";
GRANT ALL ON TABLE report TO "trac-migration";
GRANT SELECT ON TABLE report TO washort;


--
-- Name: report_id_seq; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON SEQUENCE report_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE report_id_seq FROM "trac-migration";
GRANT ALL ON SEQUENCE report_id_seq TO "trac-migration";
GRANT SELECT ON SEQUENCE report_id_seq TO washort;


--
-- Name: revision; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE revision FROM PUBLIC;
REVOKE ALL ON TABLE revision FROM "trac-migration";
GRANT ALL ON TABLE revision TO "trac-migration";
GRANT SELECT ON TABLE revision TO washort;


--
-- Name: session; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE session FROM PUBLIC;
REVOKE ALL ON TABLE session FROM "trac-migration";
GRANT ALL ON TABLE session TO "trac-migration";
GRANT SELECT ON TABLE session TO washort;


--
-- Name: session_attribute; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE session_attribute FROM PUBLIC;
REVOKE ALL ON TABLE session_attribute FROM "trac-migration";
GRANT ALL ON TABLE session_attribute TO "trac-migration";
GRANT SELECT ON TABLE session_attribute TO washort;


--
-- Name: spamfilter_bayes; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE spamfilter_bayes FROM PUBLIC;
REVOKE ALL ON TABLE spamfilter_bayes FROM "trac-migration";
GRANT ALL ON TABLE spamfilter_bayes TO "trac-migration";
GRANT SELECT ON TABLE spamfilter_bayes TO washort;


--
-- Name: spamfilter_log; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE spamfilter_log FROM PUBLIC;
REVOKE ALL ON TABLE spamfilter_log FROM "trac-migration";
GRANT ALL ON TABLE spamfilter_log TO "trac-migration";
GRANT SELECT ON TABLE spamfilter_log TO washort;


--
-- Name: spamfilter_log_id_seq; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON SEQUENCE spamfilter_log_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE spamfilter_log_id_seq FROM "trac-migration";
GRANT ALL ON SEQUENCE spamfilter_log_id_seq TO "trac-migration";
GRANT SELECT ON SEQUENCE spamfilter_log_id_seq TO washort;


--
-- Name: system; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE system FROM PUBLIC;
REVOKE ALL ON TABLE system FROM "trac-migration";
GRANT ALL ON TABLE system TO "trac-migration";
GRANT SELECT ON TABLE system TO washort;


--
-- Name: ticket; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE ticket FROM PUBLIC;
REVOKE ALL ON TABLE ticket FROM "trac-migration";
GRANT ALL ON TABLE ticket TO "trac-migration";
GRANT SELECT ON TABLE ticket TO washort;


--
-- Name: ticket_change; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE ticket_change FROM PUBLIC;
REVOKE ALL ON TABLE ticket_change FROM "trac-migration";
GRANT ALL ON TABLE ticket_change TO "trac-migration";
GRANT SELECT ON TABLE ticket_change TO washort;


--
-- Name: ticket_custom; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE ticket_custom FROM PUBLIC;
REVOKE ALL ON TABLE ticket_custom FROM "trac-migration";
GRANT ALL ON TABLE ticket_custom TO "trac-migration";
GRANT SELECT ON TABLE ticket_custom TO washort;


--
-- Name: ticket_id_seq; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON SEQUENCE ticket_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE ticket_id_seq FROM "trac-migration";
GRANT ALL ON SEQUENCE ticket_id_seq TO "trac-migration";
GRANT SELECT ON SEQUENCE ticket_id_seq TO washort;


--
-- Name: version; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE version FROM PUBLIC;
REVOKE ALL ON TABLE version FROM "trac-migration";
GRANT ALL ON TABLE version TO "trac-migration";
GRANT SELECT ON TABLE version TO washort;


--
-- Name: wiki; Type: ACL; Schema: public; Owner: trac-migration
--

REVOKE ALL ON TABLE wiki FROM PUBLIC;
REVOKE ALL ON TABLE wiki FROM "trac-migration";
GRANT ALL ON TABLE wiki TO "trac-migration";
GRANT SELECT ON TABLE wiki TO washort;


--
-- PostgreSQL database dump complete
--

