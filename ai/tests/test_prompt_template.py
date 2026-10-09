from ai.prompts.prompt_template import PromptTemplate


class TestPromptTemplateRender:
    def test_should_replace_single_variable(self):
        tmpl = PromptTemplate(template="Hello {{name}}!")
        rendered = tmpl.render({"name": "Karim"})
        assert rendered == "Hello Karim!"

    def test_should_replace_multiple_variables(self):
        tmpl = PromptTemplate(template="{{greeting}} {{name}}, welcome to {{project}}")
        rendered = tmpl.render({
            "greeting": "Welcome",
            "name": "Mohamed",
            "project": "Organizational Brain",
        })
        assert rendered == "Welcome Mohamed, welcome to Organizational Brain"

    def test_should_replace_repeated_variables(self):
        tmpl = PromptTemplate(template="{{case}} has ID {{case}}")
        rendered = tmpl.render({"case": "CASE-101"})
        assert rendered == "CASE-101 has ID CASE-101"

    def test_should_leave_unreplaced_variables_if_not_provided(self):
        tmpl = PromptTemplate(template="Hello {{name}}, your role is {{role}}")
        rendered = tmpl.render({"name": "Seif"})
        assert rendered == "Hello Seif, your role is {{role}}"

    def test_should_handle_empty_variables_dict(self):
        tmpl = PromptTemplate(template="Static content without changes")
        rendered = tmpl.render({})
        assert rendered == "Static content without changes"


class TestPromptTemplateToMessages:
    def test_should_convert_to_user_message_without_system_prompt(self):
        tmpl = PromptTemplate(template="Explain article {{article}}")
        messages = tmpl.to_messages({"article": "147"})
        assert len(messages) == 1
        assert messages[0].role == "user"
        assert messages[0].content == "Explain article 147"

    def test_should_include_system_prompt_if_provided(self):
        tmpl = PromptTemplate(
            template="Query: {{query}}",
            system_prompt="You are an Egyptian Civil Law assistant.",
        )
        messages = tmpl.to_messages({"query": "Contract breach rules"})
        assert len(messages) == 2
        assert messages[0].role == "system"
        assert messages[0].content == "You are an Egyptian Civil Law assistant."
        assert messages[1].role == "user"
        assert messages[1].content == "Query: Contract breach rules"

    def test_should_work_without_variables(self):
        tmpl = PromptTemplate(template="Standard static prompt")
        messages = tmpl.to_messages()
        assert len(messages) == 1
        assert messages[0].content == "Standard static prompt"


class TestPromptTemplateExtractVariables:
    def test_should_extract_single_variable(self):
        tmpl = PromptTemplate(template="User is {{username}}")
        assert tmpl.extract_variables() == ["username"]

    def test_should_extract_multiple_variables(self):
        tmpl = PromptTemplate(template="{{a}} plus {{b}} equals {{c}}")
        assert tmpl.extract_variables() == ["a", "b", "c"]

    def test_should_extract_unique_variables_only(self):
        tmpl = PromptTemplate(template="{{tag}} and another {{tag}} with {{other}}")
        assert tmpl.extract_variables() == ["tag", "other"]

    def test_should_return_empty_list_if_no_variables(self):
        tmpl = PromptTemplate(template="No placeholders here")
        assert tmpl.extract_variables() == []


class TestPromptTemplateProperties:
    def test_should_return_template_string(self):
        tmpl = PromptTemplate(template="Raw template")
        assert tmpl.template == "Raw template"

    def test_should_return_system_prompt_if_set(self):
        tmpl = PromptTemplate(template="Prompt", system_prompt="System instructions")
        assert tmpl.system_prompt == "System instructions"

    def test_should_return_none_for_system_prompt_if_not_set(self):
        tmpl = PromptTemplate(template="Prompt")
        assert tmpl.system_prompt is None

    def test_should_return_metadata_if_set(self):
        meta = {"domain": "legal", "version": 1}
        tmpl = PromptTemplate(template="Prompt", metadata=meta)
        assert tmpl.metadata == meta
