import typing as t

from pydantic import BaseModel, PrivateAttr
from typing import Optional, Dict, Any

if t.TYPE_CHECKING:  # avoid import cycle at runtime
    from .client import Client
from .structs import (
    JSONDict,
    Diagnostic,
    MessageType,
    MessageActionItem,
    CompletionItem,
    CompletionList,
    TextEdit,

    MarkupContent,
    Range,
    Location,
    # NEW ########
    MarkedString,
    ParameterInformation,
    SignatureInformation,
    LocationLink,
    CallHierarchyItem,
    SymbolInformation,
    Registration,
    DocumentSymbol,
    WorkspaceFolder,
    ProgressToken,
    ProgressValue,
    WorkDoneProgressBeginValue,
    WorkDoneProgressReportValue,
    WorkDoneProgressEndValue,
    ConfigurationItem,
)

Id = t.Union[int, str]


class Event(BaseModel):
    pass


class ResponseError(Event):
    message_id: t.Optional[Id] = None
    code: int
    message: str
    data: t.Optional[ t.Union[
        str,
        int, float,
        bool,
        list,
        JSONDict,
        None,
    ]] = None


class ServerRequest(Event):
    _client: "Client" = PrivateAttr()
    _id: Id = PrivateAttr()


class ServerNotification(Event):
    pass


class Initialized(Event):
    capabilities: JSONDict


class Shutdown(Event):
    pass


class ShowMessage(ServerNotification):
    type: MessageType
    message: str


class ShowMessageRequest(ServerRequest):
    type: MessageType
    message: str
    actions: t.Optional[t.List[MessageActionItem]] = None

    def reply(self, action: t.Optional[MessageActionItem] = None) -> None:
        """
        Reply to the ShowMessageRequest with the user's selection.

        No bytes are actually returned from this method, the reply's bytes
        are added to the client's internal send buffer.
        """
        self._client._send_response(
            id=self._id, result=action.model_dump() if action is not None else None
        )


class LogMessage(ServerNotification):
    type: MessageType
    message: str

class WorkDoneProgressCreate(ServerRequest):
    token: ProgressToken

    def reply(self) -> None:
        self._client._send_response(id=self._id, result=None)

class Progress(ServerNotification):
    token: ProgressToken
    value: ProgressValue

class WorkDoneProgress(Progress):
    pass

class WorkDoneProgressBegin(WorkDoneProgress):
    value: WorkDoneProgressBeginValue

class WorkDoneProgressReport(WorkDoneProgress):
    value: WorkDoneProgressReportValue

class WorkDoneProgressEnd(WorkDoneProgress):
    value: WorkDoneProgressEndValue


# XXX: should these two be just Events or?
class Completion(Event):
    message_id: Id
    #completion_list: t.Optional[CompletionList]
    completion_list: t.Optional[t.Dict[str, t.Any]] = None  # make it raw dict (optimization)


# XXX: not sure how to name this event.
class WillSaveWaitUntilEdits(Event):
    edits: t.Optional[t.List[TextEdit]] = None


class PublishDiagnostics(ServerNotification):
    uri: str
    diagnostics: t.List[Diagnostic]


""" Hover:
    * contents: MarkedString | MarkedString[] | MarkupContent;
    * range?: Range;
"""
class Hover(Event):
    message_id: t.Optional[Id] = None # custom...
    contents: t.Union[
            t.List[t.Union[MarkedString, str]],
            MarkedString, # .language, .value
            MarkupContent, # kind: MarkupKind, value: str
            str,
            ]
    range: t.Optional[Range] = None

    # DBG
    def m_str(self):
        def item_str(item): #SKIP
            if isinstance(item, MarkedString):
                return f'[{item.language}]\n{item.value}'
            elif isinstance(item, MarkupContent):
                return f'[{item.kind}]\n{item.value}'
            return item # str

        if isinstance(self.contents, list):
            return '\n'.join((item_str(item) for item in self.contents))
        return item_str(self.contents)

class SignatureHelp(Event):
    message_id: t.Optional[Id] = None # custom...
    signatures: t.List[SignatureInformation]
    activeSignature: t.Optional[int] = None
    activeParameter: t.Optional[int] = None

    def get_hint_str(self):
        if len(self.signatures) == 0:
            return None
        active_sig = self.activeSignature or 0
        sig = self.signatures[active_sig]
        return sig.label
        
    def get_signatures(self):
        if len(self.signatures) == 0:
            return None
        return self.signatures, self.activeSignature, self.activeParameter


class SemanticTokens(Event):
    message_id: t.Optional[Id] = None
    resultId: t.Optional[str] = None
    data: t.List[int]
    

class Definition(Event):
    message_id: t.Optional[Id] = None
    result: t.Union[
        Location,
        t.List[t.Union[Location, LocationLink]],
        None] = None


# result is a list, so putting i a custom class
class References(Event):
    message_id: t.Optional[Id] = None
    result: t.Union[t.List[Location], None] = None


class MCallHierarchItems(Event):
    result: t.Union[t.List[CallHierarchyItem], None] = None


class Implementation(Event):
    message_id: t.Optional[Id] = None
    result: t.Union[
        Location,
        t.List[t.Union[Location, LocationLink]],
        None] = None


class MWorkspaceSymbols(Event):
    result: t.Union[t.List[SymbolInformation], None] = None


class MDocumentSymbols(Event):
    message_id: t.Optional[Id] = None # custom...
    result: t.Union[t.List[SymbolInformation], t.List[DocumentSymbol], None] = None


class Declaration(Event):
    message_id: t.Optional[Id] = None
    result: t.Union[
        Location,
        t.List[t.Union[Location, LocationLink]],
        None] = None


class TypeDefinition(Event):
    message_id: t.Optional[Id] = None
    result: t.Union[
        Location,
        t.List[t.Union[Location, LocationLink]],
        None] = None


class RegisterCapabilityRequest(ServerRequest):
    registrations: t.List[Registration]

    def reply(self) -> None:
        self._client._send_response(id=self._id, result={})

class DocumentFormatting(Event):
    message_id: t.Optional[Id] = None # custom...
    result: t.Union[t.List[TextEdit], None] = None


class WorkspaceFolders(ServerRequest):
    result: None = None

    def reply(self, folders: t.Optional[t.List[WorkspaceFolder]] = None) -> None:
        """
        Reply to the WorkspaceFolder with workspace folders.

        No bytes are actually returned from this method, the reply's bytes
        are added to the client's internal send buffer.
        """
        self._client._send_response(
            id=self._id, result=[f.model_dump() for f in folders] if folders is not None else None
        )

class ConfigurationRequest(ServerRequest):
    items: t.List[ConfigurationItem]

    def reply(self, result=t.List[t.Any]) -> None:
        self._client._send_response(id=self._id,  result=result)

class Metadata(Event):
    message_id: int
    result: Optional[Dict[str, Any]] = None
    
