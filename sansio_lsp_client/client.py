import enum
#import pprint
import typing as t

from pydantic import ValidationError, TypeAdapter

from .events import (
    Completion,
    ConfigurationRequest,
    Declaration,
    Definition,
    DocumentFormatting,
    Event,
    Hover,
    Implementation,
    Initialized,
    LogMessage,
    MCallHierarchItems,
    MDocumentSymbols,
    MFoldingRanges,
    MInlayHints,
    Metadata,
    MWorkspaceSymbols,
    MethodResponse,
    Progress,
    PublishDiagnostics,
    References,
    RegisterCapabilityRequest,
    ResponseError,
    SemanticTokens,
    ServerNotification,
    ServerRequest,
    ShowMessage,
    ShowMessageRequest,
    Shutdown,
    SignatureHelp,
    TypeDefinition,
    WillSaveWaitUntilEdits,
    WorkDoneProgress,
    WorkDoneProgressBegin,
    WorkDoneProgressCreate,
    WorkDoneProgressEnd,
    WorkDoneProgressReport,
    WorkspaceEdit,
    WorkspaceFolders,
    WorkspaceProjectInitializationComplete,
)
from .io_handler import _make_request, _make_response, _parse_messages
from .structs import (
    CompletionContext,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    FormattingOptions,
    Id,
    JSONDict,
    JSONList,
    MWorkDoneProgressKind,
    Range,
    Request,
    Response,
    SymbolKind,
    TextDocumentContentChangeEvent,
    TextDocumentEdit,
    TextDocumentIdentifier,
    TextDocumentItem,
    TextDocumentPosition,
    TextDocumentSaveReason,
    TextEdit,
    VersionedTextDocumentIdentifier,
    WorkspaceFolder,
)


class ClientState(enum.Enum):
    NOT_INITIALIZED = enum.auto()
    WAITING_FOR_INITIALIZED = enum.auto()
    NORMAL = enum.auto()
    WAITING_FOR_SHUTDOWN = enum.auto()
    SHUTDOWN = enum.auto()
    EXITED = enum.auto()

#NOTE: Server capabilitie: resolveProvider - info about completion item -- can't use?
CAPABILITIES: JSONDict = {
    "textDocument": {
        "synchronization": {
            "didSave": True,
            #'willSaveWaitUntil': True,
            "dynamicRegistration": True,
            #'willSave': True
        },
        "publishDiagnostics": {
            "relatedInformation": True,
            "tagSupport": {"valueSet": [1,2]}
        },
        "completion": {
            "dynamicRegistration": True,
            "completionItem": {"snippetSupport": True},
            "completionItemKind": {"valueSet": list(CompletionItemKind)},
            "contextSupport": True,
        },
        "hover": {
            "dynamicRegistration": True,
            "contentFormat": ["markdown", "plaintext"],
        },
        "foldingRange": {
            "dynamicRegistration": True,
        },
        "inlayHint": {
            "dynamicRegistration": True,
        },
        "definition": {"dynamicRegistration": True, "linkSupport": True},
        "signatureHelp": {
            "dynamicRegistration": True,
            "signatureInformation": {
                "parameterInformation": {
                    "labelOffsetSupport": True  # substring from label
                },
                "documentationFormat": ["markdown", "plaintext"],
                "activeParameterSupport": True
            },
        },
        "implementation": {"linkSupport": True, "dynamicRegistration": True},
        "references": {"dynamicRegistration": True},
        "callHierarchy": {"dynamicRegistration": True},
        "declaration": {"linkSupport": True, "dynamicRegistration": True},
        "typeDefinition": {"linkSupport": True, "dynamicRegistration": True},
        "formatting": {"dynamicRegistration": True},
        "rangeFormatting": {"dynamicRegistration": True},
        "rename": {"dynamicRegistration": True},
        "documentSymbol": {
            "hierarchicalDocumentSymbolSupport": True,
            "dynamicRegistration": True,
            "symbolKind": {"valueSet": list(SymbolKind)},
        },
    },
    "window": {
        "showMessage": {
            # TODO 'messageActionItem':...
            #"messageActionItem": {
                #"additionalPropertiesSupport": True
            #}
        },
        "workDoneProgress": True,
    },
    "workspace": {
        "symbol": {
            "dynamicRegistration": True,
            "symbolKind": {"valueSet": list(SymbolKind)},
        },
        "workspaceFolders": True,
        # TODO 'workspaceEdit':..., #'applyEdit':..., 'executeCommand':...,
        #"workspaceEdit": {
            #"failureHandling": "abort",
            #"documentChanges": True
        #},
        #"applyEdit": True,
        #"executeCommand": {},
        "configuration": True,
        "didChangeConfiguration": {"dynamicRegistration": True},
    },
}


class Client:
    # TODO: Save the encoding given here.
    def __init__(
        self,
        process_id: t.Optional[int] = None,
        root_uri: t.Optional[str] = None,
        workspace_folders: t.Optional[t.List[WorkspaceFolder]] = None,
        trace: str = "off",
        settings = {},
    ) -> None:
        self._state = ClientState.NOT_INITIALIZED

        # Used to save data as it comes in (from `recieve_bytes`) until we have
        # a full request.
        self._recv_buf = bytearray()

        # Things that we still need to send.
        self._send_buf = bytearray()

        # Keeps track of which IDs match to which unanswered requests.
        self._unanswered_requests: t.Dict[Id, Request] = {}

        # Just a simple counter to make sure we have unique IDs. We could make
        # sure that this fits into a JSONRPC Number, seeing as Python supports
        # bignums, but I think that's an unlikely enough case that checking for
        # it would just litter the code unnecessarily.
        self._id_counter = 0

        # Store type of '$/progress' for parsing
        self._progress_tokens_map: t.Dict[ProgressToken, t.Type[Progress]] = {}

        # We'll just immediately send off an "initialize" request.
        self._send_request(
            method="initialize",
            params={
                "processId": process_id,
                "rootUri": root_uri,
                "workspaceFolders": (
                    None
                    if workspace_folders is None
                    else [f.model_dump() for f in workspace_folders]
                ),
                "trace": trace,
                "capabilities": CAPABILITIES,
                "initializationOptions": settings,
            },
        )
        self._state = ClientState.WAITING_FOR_INITIALIZED

        # prepare configuration for sending via "workspace/didChangeConfiguration"
        self.settings = settings

    @property
    def state(self) -> ClientState:
        return self._state

    @property
    def is_initialized(self) -> bool:
        return (
            self._state != ClientState.NOT_INITIALIZED
            and self._state != ClientState.WAITING_FOR_INITIALIZED
        )

    def _send_request(self, method: str, params: t.Optional[JSONDict] = None) -> Id:
        id: Id = self._id_counter
        self._id_counter += 1

        self._send_buf += _make_request(method=method, params=params, id=id)
        self._unanswered_requests[id] = Request(id=id, method=method, params=params)
        return id

    def _send_notification(
        self, method: str, params: t.Optional[JSONDict] = None
    ) -> None:
        self._send_buf += _make_request(method=method, params=params)

    def _send_response(
        self,
        id: Id,
        result: t.Optional[t.Union[JSONDict, JSONList]] = None,
        error: t.Optional[JSONDict] = None,
    ) -> None:
        self._send_buf += _make_response(id=id, result=result, error=error)

    # response from server
    def _handle_response(self, response: Response) -> Event:
        assert response.id is not None
        request = self._unanswered_requests.pop(response.id)

        # FIXME: The errors have meanings.
        if response.error is not None:
            #raise RuntimeError("Response error!\n\n" + pprint.pformat(response.error))
            err = ResponseError.model_validate(response.error)
            err.message_id = response.id
            return err

        event: Event
        
        method = request.method

        if method == "initialize":
            assert self._state == ClientState.WAITING_FOR_INITIALIZED
            self._send_notification(
              "initialized", params={}
            )  # params=None doesn't work with gopls
            self._send_notification("workspace/didChangeConfiguration", params={
                "settings": self.settings
            })
            event = Initialized.model_validate(response.result)
            self._state = ClientState.NORMAL

        elif method == "shutdown":
            assert self._state == ClientState.WAITING_FOR_SHUTDOWN
            event = Shutdown()
            self._state = ClientState.SHUTDOWN

        elif method == "textDocument/completion":
            completion_list = None

            if isinstance(response.result, dict):
                completion_list = response.result
            elif isinstance(response.result, list):
                completion_list = {
                    'isIncomplete': 'false',
                    'items': response.result,
                }
            
            ## ! parse_obj/model_validate is expensive and not really needed.
            #try:
            #    completion_list = CompletionList.model_validate(response.result)
            #except ValidationError:
            #    try:
            #        list_adapter = TypeAdapter(t.List[CompletionItem])
            #        completion_list = CompletionList(
            #            isIncomplete=False,
            #            items=list_adapter.validate_python(response.result),
            #        )
            #    except ValidationError:
            #        assert response.result is None

            event = Completion(
                message_id=response.id, completion_list=completion_list
            )

        elif method == "textDocument/willSaveWaitUntil":
            event = WillSaveWaitUntilEdits(
                edits=TypeAdapter(t.List[TextEdit]).validate_python(response.result)
            )

        elif method == "textDocument/hover":
            if response.result is not None:
                event = Hover.model_validate(response.result)
            else:
                event = Hover(contents=[])  # null response
            event.message_id = response.id

        elif method == "textDocument/foldingRange":
            event = MFoldingRanges(
                message_id=response.id,
                result=response.result if response.result is not None else [],
            )

        elif method == "textDocument/signatureHelp":
            if response.result is not None:
                event = SignatureHelp.model_validate(response.result)
            else:
                event = SignatureHelp(signatures=[])  # null response
            event.message_id = response.id

        elif method == "textDocument/documentSymbol":
            event = MDocumentSymbols(
                message_id=response.id,
                result=response.result if response.result is not None else [],
            )

        elif method == "textDocument/inlayHint":
            event = TypeAdapter(MInlayHints).validate_python(response)
            event.message_id = response.id

        elif method == "textDocument/rename":
            if response.result is not None and isinstance(response.result, dict):
                if "documentChanges" in response.result:
                    document_changes = [
                        TextDocumentEdit.model_validate(change)
                        for change in response.result["documentChanges"]
                    ]
                    event = WorkspaceEdit(
                        message_id=response.id, documentChanges=document_changes
                    )
                elif "changes" in response.result:
                    event = WorkspaceEdit(
                        message_id=response.id, changes=response.result["changes"]
                    )
                else:
                    event = WorkspaceEdit(message_id=response.id)
            else:
                event = WorkspaceEdit(message_id=response.id)

        elif method == "textDocument/semanticTokens/full":
            if response.result is None:
                event = SemanticTokens(data=[])
            else:
                event = SemanticTokens.model_validate(response.result)
            event.message_id = response.id

        #GOTOs
        elif method == "textDocument/definition":
            event = TypeAdapter(Definition).validate_python(
                {"result": response.result}
            )
            event.message_id = response.id

        elif method == "textDocument/references":
            event = TypeAdapter(References).validate_python(
                {"result": response.result}
            )

        elif method == "textDocument/implementation":
            event = TypeAdapter(Implementation).validate_python(
                {"result": response.result}
            )

        elif method == "textDocument/declaration":
            event = TypeAdapter(Declaration).validate_python(
                {"result": response.result}
            )

        elif method == "textDocument/typeDefinition":
            event = TypeAdapter(TypeDefinition).validate_python(
                {"result": response.result}
            )

        elif method == "textDocument/prepareCallHierarchy":
            event = TypeAdapter(MCallHierarchItems).validate_python(
                {"result": response.result}
            )

        elif method in ("textDocument/formatting", "textDocument/rangeFormatting"):
            event = TypeAdapter(DocumentFormatting).validate_python(
                {"result": response.result}
            )

        # WORKSPACE
        elif method == "workspace/symbol":
            event = TypeAdapter(MWorkspaceSymbols).validate_python(
                {"result": response.result}
            )

        elif method == "o#/metadata":
            metadata_result = response.result if isinstance(response.result, dict) else None
            event = Metadata(message_id=response.id, result=metadata_result)

        else:
            raise NotImplementedError((response, request))

        if isinstance(event, MethodResponse):
            event.message_id = response.id

        return event

    # request from server
    def _handle_request(self, request: Request) -> Event:
        def parse_request(event_cls: t.Type[Event]) -> Event:
            if issubclass(event_cls, ServerRequest):
                event = TypeAdapter(event_cls).validate_python(request.params)
                assert request.id is not None
                event._id = request.id
                event._client = self
                return event
            elif issubclass(event_cls, ServerNotification):
                if isinstance(request.params, dict):
                    return TypeAdapter(event_cls).validate_python(request.params)
                else:
                    return TypeAdapter(event_cls).validate_python({})
            else:
                raise TypeError(
                    "`event_cls` must be a subclass of ServerRequest"
                    " or ServerNotification"
                )

        if request.method == "workspace/workspaceFolders":
            # return parse_request(WorkspaceFolders)
            # ... We don't need to parse WorkspaceFolders server's request!
            # because according to LSP specs "params: none"
            # Just create empty event and return it
            event = WorkspaceFolders(result=None)
            event._id = request.id
            event._client = self
            return event
        elif request.method == "workspace/configuration":
            event = parse_request(ConfigurationRequest)
            assert isinstance(event, ConfigurationRequest)
            return event
        elif request.method == "workspace/projectInitializationComplete":
            event = parse_request(WorkspaceProjectInitializationComplete)
            assert isinstance(event, WorkspaceProjectInitializationComplete)
            return event
        elif request.method == "window/showMessage":
            event = parse_request(ShowMessage)
            assert isinstance(event, ShowMessage)
            return event
        elif request.method == "window/showMessageRequest":
            event = parse_request(ShowMessageRequest)
            assert isinstance(event, ShowMessageRequest)
            return event
        elif request.method == "window/logMessage":
            event = parse_request(LogMessage)
            assert isinstance(event, LogMessage)
            return event
        elif request.method == "textDocument/publishDiagnostics":
            event = parse_request(PublishDiagnostics)
            assert isinstance(event, PublishDiagnostics)
            return event
        elif request.method == "window/workDoneProgress/create":
            ev = parse_request(WorkDoneProgressCreate)
            self._progress_tokens_map[request.params['token']] = WorkDoneProgress
            return parse_request(WorkDoneProgressCreate)
        elif request.method == "client/registerCapability":
            event = parse_request(RegisterCapabilityRequest)
            assert isinstance(event, RegisterCapabilityRequest)
            return event

        elif request.method == "$/progress":
            progress_type = self._progress_tokens_map.get(request.params['token'])
            
            # if "window/workDoneProgress/create" request from server was missing -
            # pretend it actually was already recieved. i think there is no harm in that.
            # such server bugs must be silently ignored without crashing our plugin.
            if progress_type is None:
                # Gracefully handle servers that forget to send workDoneProgress/create
                self._progress_tokens_map[request.params['token']] = WorkDoneProgress
                progress_type = WorkDoneProgress

            if progress_type == WorkDoneProgress:
                kind = request.params['value']['kind']
                kind = MWorkDoneProgressKind(kind)

                if kind == MWorkDoneProgressKind.BEGIN:
                    return parse_request(WorkDoneProgressBegin)
                elif kind == MWorkDoneProgressKind.REPORT:
                    return parse_request(WorkDoneProgressReport)
                elif kind == MWorkDoneProgressKind.END:
                    del self._progress_tokens_map[request.params["token"]] # prevent the dictionary from growing indefinitely.
                    return parse_request(WorkDoneProgressEnd)
                else:
                    raise ValueError(f"Unknown progress kind: {kind}")



        else:
            raise NotImplementedError(request)

    def recv(self, data: bytes, errors: t.Optional[t.List[Exception]] = None) -> t.List[Event]:
        self._recv_buf += data

        # _parse_messages deletes consumed data from self._recv_buf
        messages = list(_parse_messages(self._recv_buf))

        events: t.List[Event] = []
        for message in messages:
            try:
                if isinstance(message, Response):
                    events.append(self._handle_response(message))
                elif isinstance(message, Request):
                    events.append(self._handle_request(message))
                else:
                    raise RuntimeError("Unexpected message type")
            except Exception as exc:
                if errors is not None:
                    errors.append(exc)

        return events

    def send(self) -> bytes:
        send_buf = self._send_buf[:]
        self._send_buf.clear()
        return send_buf

    def shutdown(self) -> None:
        assert self._state == ClientState.NORMAL
        self._send_request(method="shutdown")
        self._state = ClientState.WAITING_FOR_SHUTDOWN

    def exit(self) -> None:
        assert self._state == ClientState.SHUTDOWN
        # TODO: figure out why params={} is needed
        self._send_notification(method="exit", params={})
        self._state = ClientState.EXITED

    def cancel_last_request(self) -> None:
        self._send_notification(
            method="$/cancelRequest", params={"id": self._id_counter - 1}
        )

    def did_open(self, text_document: TextDocumentItem) -> None:
        assert self._state == ClientState.NORMAL
        self._send_notification(
            method="textDocument/didOpen",
            params={"textDocument": text_document.model_dump()},
        )

    def did_change(
        self,
        text_document: VersionedTextDocumentIdentifier,
        content_changes: t.List[TextDocumentContentChangeEvent],
    ) -> None:
        assert self._state == ClientState.NORMAL
        self._send_notification(
            method="textDocument/didChange",
            params={
                "textDocument": text_document.model_dump(),
                "contentChanges": [evt.model_dump() for evt in content_changes],
            },
        )

    def did_change_configuration(self, settings: t.Any) -> None:
        assert self._state == ClientState.NORMAL
        self._send_notification(
            method="workspace/didChangeConfiguration", params={"settings": settings}
        )

    def will_save(
        self, text_document: TextDocumentIdentifier, reason: TextDocumentSaveReason
    ) -> None:
        assert self._state == ClientState.NORMAL
        self._send_notification(
            method="textDocument/willSave",
            params={"textDocument": text_document.model_dump(), "reason": reason.value},
        )

    def will_save_wait_until(
        self, text_document: TextDocumentIdentifier, reason: TextDocumentSaveReason
    ) -> None:
        assert self._state == ClientState.NORMAL
        self._send_request(
            method="textDocument/willSaveWaitUntil",
            params={"textDocument": text_document.model_dump(), "reason": reason.value},
        )

    def did_save(
        self, text_document: TextDocumentIdentifier, text: t.Optional[str] = None
    ) -> None:
        assert self._state == ClientState.NORMAL
        params: t.Dict[str, t.Any] = {"textDocument": text_document.model_dump()}
        if text is not None:
            params["text"] = text
        self._send_notification(method="textDocument/didSave", params=params)

    def did_close(self, text_document: TextDocumentIdentifier) -> None:
        assert self._state == ClientState.NORMAL
        self._send_notification(
            method="textDocument/didClose",
            params={"textDocument": text_document.model_dump()},
        )

    def did_change_workspace_folders(
        self, added: t.List[WorkspaceFolder], removed: t.List[WorkspaceFolder]
    ) -> None:
        assert self._state == ClientState.NORMAL
        params = {
            "added": [f.model_dump() for f in added],
            "removed": [f.model_dump() for f in removed],
        }
        self._send_notification(
            method="workspace/didChangeWorkspaceFolders", params=params
        )

    def completion(
        self,
        text_document_position: TextDocumentPosition,
        context: t.Optional[CompletionContext] = None,
    ) -> Id:
        assert self._state == ClientState.NORMAL
        params = {}
        params.update(text_document_position.model_dump())
        if context is not None:
            params.update( {
                'context': context.model_dump(exclude_unset=True)
            } )
        return self._send_request(method="textDocument/completion", params=params)

    def semantic_tokens(
        self,
        text_document: TextDocumentIdentifier,
    ) -> Id:
        assert self._state == ClientState.NORMAL
        return self._send_request(
            method="textDocument/semanticTokens/full",
            params={"textDocument": text_document.model_dump()},
        )

    def rename(
        self,
        text_document_position: TextDocumentPosition,
        new_name: str,
    ) -> Id:
        assert self._state == ClientState.NORMAL
        params = {}
        params.update(text_document_position.model_dump())
        params["newName"] = new_name
        return self._send_request(method="textDocument/rename", params=params)

    def hover(self, text_document_position: TextDocumentPosition) -> Id:
        assert self._state == ClientState.NORMAL
        return self._send_request(
            method="textDocument/hover", params=text_document_position.model_dump()
        )

    def folding_range(self, text_document: TextDocumentIdentifier) -> Id:
        assert self._state == ClientState.NORMAL
        return self._send_request(
            method="textDocument/foldingRange",
            params={"textDocument": text_document.model_dump()},
        )

    def signatureHelp(self, text_document_position: TextDocumentPosition) -> Id:
        assert self._state == ClientState.NORMAL
        return self._send_request(
            method="textDocument/signatureHelp",
            params=text_document_position.model_dump(),
        )

    def definition(self, text_document_position: TextDocumentPosition) -> Id:
        assert self._state == ClientState.NORMAL
        return self._send_request(
            method="textDocument/definition", params=text_document_position.model_dump()
        )

    def declaration(self, text_document_position: TextDocumentPosition) -> Id:
        assert self._state == ClientState.NORMAL
        return self._send_request(
            method="textDocument/declaration",
            params=text_document_position.model_dump(),
        )

    def inlay_hint(self, text_document: TextDocumentIdentifier, range: Range) -> Id:
        assert self._state == ClientState.NORMAL
        return self._send_request(
            method="textDocument/inlayHint",
            params={
                "textDocument": text_document.model_dump(),
                "range": range.model_dump(),
            },
        )

    def typeDefinition(self, text_document_position: TextDocumentPosition) -> Id:
        assert self._state == ClientState.NORMAL
        return self._send_request(
            method="textDocument/typeDefinition",
            params=text_document_position.model_dump(),
        )

    def references(self, text_document_position: TextDocumentPosition) -> Id:
        assert self._state == ClientState.NORMAL
        params = {
            "context": {"includeDeclaration": True},
            **text_document_position.model_dump(),
        }
        return self._send_request(method="textDocument/references", params=params)

    # TODO incomplete
    def prepareCallHierarchy(self, text_document_position: TextDocumentPosition) -> Id:
        assert self._state == ClientState.NORMAL
        return self._send_request(
            method="textDocument/prepareCallHierarchy",
            params=text_document_position.model_dump(),
        )

    def implementation(self, text_document_position: TextDocumentPosition) -> Id:
        assert self._state == ClientState.NORMAL
        return self._send_request(
            method="textDocument/implementation",
            params=text_document_position.model_dump(),
        )

    def workspace_symbol(self, query: str = "") -> Id:
        assert self._state == ClientState.NORMAL
        return self._send_request(method="workspace/symbol", params={"query": query})

    def documentSymbol(self, text_document: TextDocumentIdentifier) -> Id:
        assert self._state == ClientState.NORMAL
        return self._send_request(
            method="textDocument/documentSymbol",
            params={"textDocument": text_document.model_dump()},
        )

    def formatting(
        self, text_document: TextDocumentIdentifier, options: FormattingOptions
    ) -> Id:
        assert self._state == ClientState.NORMAL
        params = {
            "textDocument": text_document.model_dump(),
            "options": options.model_dump(),
        }
        return self._send_request(method="textDocument/formatting", params=params)

    def rangeFormatting(
        self,
        text_document: TextDocumentIdentifier,
        range: Range,
        options: FormattingOptions,
    ) -> Id:
        assert self._state == ClientState.NORMAL
        params = {
            "textDocument": text_document.model_dump(),
            "range": range.model_dump(),
            "options": options.model_dump(),
        }
        return self._send_request(method="textDocument/rangeFormatting", params=params)

    def metadata(self, params):
        return self._send_request(method="o#/metadata", params=params)

