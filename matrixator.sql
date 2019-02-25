-- Database generated with pgModeler (PostgreSQL Database Modeler).
-- pgModeler  version: 0.9.1
-- PostgreSQL version: 10.0
-- Project Site: pgmodeler.io
-- Model Author: ---

-- object: matrixator | type: ROLE --
-- DROP ROLE IF EXISTS matrixator;
CREATE ROLE matrixator WITH 
	CREATEDB
	ENCRYPTED PASSWORD 'abrakadabramatrix';
-- ddl-end --


-- Database creation must be done outside a multicommand file.
-- These commands were put in this file only as a convenience.
-- -- object: matrixator | type: DATABASE --
-- -- DROP DATABASE IF EXISTS matrixator;
-- CREATE DATABASE matrixator
-- 	OWNER = matrixator;
-- -- ddl-end --
-- 

-- object: public.play | type: TABLE --
-- DROP TABLE IF EXISTS public.play CASCADE;
CREATE TABLE public.play(
	id bigserial NOT NULL,
	status character varying NOT NULL,
	host character varying NOT NULL,
	ts timestamptz NOT NULL DEFAULT now(),
	name character varying,
	CONSTRAINT play_pk PRIMARY KEY (id)

);
-- ddl-end --
ALTER TABLE public.play OWNER TO matrixator;
-- ddl-end --

-- object: play_status_idx | type: INDEX --
-- DROP INDEX IF EXISTS public.play_status_idx CASCADE;
CREATE INDEX play_status_idx ON public.play
	USING btree
	(
	  status
	);
-- ddl-end --

-- object: play_ts_idx | type: INDEX --
-- DROP INDEX IF EXISTS public.play_ts_idx CASCADE;
CREATE INDEX play_ts_idx ON public.play
	USING btree
	(
	  ts ASC NULLS LAST
	);
-- ddl-end --

-- object: play_host_idx | type: INDEX --
-- DROP INDEX IF EXISTS public.play_host_idx CASCADE;
CREATE INDEX play_host_idx ON public.play
	USING btree
	(
	  host
	);
-- ddl-end --

-- object: public.task | type: TABLE --
-- DROP TABLE IF EXISTS public.task CASCADE;
CREATE TABLE public.task(
	id bigserial NOT NULL,
	result jsonb NOT NULL,
	duration tsrange NOT NULL,
	status character varying NOT NULL,
	id_play bigserial,
	CONSTRAINT task_pk PRIMARY KEY (id)

);
-- ddl-end --
ALTER TABLE public.task OWNER TO postgres;
-- ddl-end --

-- object: play_fk | type: CONSTRAINT --
-- ALTER TABLE public.task DROP CONSTRAINT IF EXISTS play_fk CASCADE;
ALTER TABLE public.task ADD CONSTRAINT play_fk FOREIGN KEY (id_play)
REFERENCES public.play (id) MATCH FULL
ON DELETE CASCADE ON UPDATE CASCADE;
-- ddl-end --


