 <!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="mobile-web-app-capable" content="yes">
<link rel="apple-touch-icon" sizes="180x180" href="https://poznamky.pernicka.cz/icons/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="https://poznamky.pernicka.cz/icons/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="https://poznamky.pernicka.cz/icons/favicon-16x16.png">
<link rel="manifest" href="https://poznamky.pernicka.cz/icons/site.webmanifest">
<link rel="mask-icon" href="https://poznamky.pernicka.cz/icons/safari-pinned-tab.svg" color="#b51f08">
<link rel="shortcut icon" href="https://poznamky.pernicka.cz/icons/favicon.ico">
<meta name="apple-mobile-web-app-title" content="HedgeDoc - Collaborative markdown notes">
<meta name="application-name" content="HedgeDoc - Collaborative markdown notes">
<meta name="msapplication-TileColor" content="#b51f08">
<meta name="msapplication-config" content="https://poznamky.pernicka.cz/icons/browserconfig.xml">
<meta name="theme-color" content="#b51f08">



<meta property="og:title" content="LAG 2 definice / formulace tvrzení - HedgeDoc">



<meta property="og:type" content="website">

<meta property="og:image" content="https://poznamky.pernicka.cz/icons/android-chrome-512x512.png">
<meta property="og:image:alt" content="HedgeDoc logo">
<meta property="og:image:type" content="image/png">

<base href="https://poznamky.pernicka.cz/">
<title>LAG 2 definice / formulace tvrzení - HedgeDoc</title>
<link rel="stylesheet" href='https://poznamky.pernicka.cz/build/emojify.js/dist/css/basic/emojify.min.css'>
<link href="build/font-pack.51d576c9ea0a7705d2e0.css" rel="stylesheet"><link href="build/2.04010c738e6d668e6e08.css" rel="stylesheet"><link href="build/3.b67314821de89ccff48b.css" rel="stylesheet"><link href="build/index-styles-pack.f8ae33429b581d4e1171.css" rel="stylesheet"><link href="build/23.d59661af151ee860e569.css" rel="stylesheet"><link href="build/index-styles.69f33f427763810ebdcf.css" rel="stylesheet"><link href="build/1.1666d9d869a0532d9bce.css" rel="stylesheet"><link href="build/index.d22d802e5e88a36eefc1.css" rel="stylesheet">

</head>

<body translate="no">
    <nav class="navbar navbar-default navbar-fixed-top unselectable hidden-print">
    <!-- Brand and toggle get grouped for better mobile display -->
    <div class="navbar-header">
        <div class="pull-right" style="margin-top: 17px; color: #777;">
            <div class="visible-xs">&nbsp;</div>
            <div class="visible-sm">&nbsp;</div>
            <div class="visible-md">&nbsp;</div>
            <div class="visible-lg">&nbsp;</div>
        </div>
        <div class="nav-mobile nav-status visible-xs" id="short-online-user-list">
            <a class="ui-short-status" data-toggle="dropdown"><span class="label label-danger"><i class="fa fa-plug"></i> </span>
            </a>
            <ul class="dropdown-menu list" role="menu" aria-labelledby="menu">
            </ul>
        </div>
        <a class="navbar-brand pull-left header-brand" href="https://poznamky.pernicka.cz/" title="HedgeDoc (formerly CodiMD)">
            <img src="https://poznamky.pernicka.cz/banner/banner_h_bw.svg" alt="HedgeDoc" class="h-100 no-night">
            <img src="https://poznamky.pernicka.cz/banner/banner_h_wb.svg" alt="HedgeDoc" class="h-100 night">
        </a>
        <div class="nav-mobile pull-right visible-xs">
            <a data-toggle="dropdown" class="btn btn-link">
                <i class="fa fa-caret-down"></i>
            </a>
            <ul class="dropdown-menu list" role="menu" aria-labelledby="menu">
                <li role="presentation"><a role="menuitem" class="ui-new" tabindex="-1" href="https://poznamky.pernicka.cz/new" target="_blank" rel="noopener"><i class="fa fa-plus fa-fw"></i> New</a>
                </li>
                <li role="presentation"><a role="menuitem" class="ui-publish" tabindex="-1" href="#" target="_blank" rel="noopener"><i class="fa fa-share-square-o fa-fw"></i> Publish</a>
                </li>
                <li class="divider"></li>
                <li class="dropdown-header">Extra</li>
                <li role="presentation"><a role="menuitem" class="ui-extra-revision" tabindex="-1" data-toggle="modal" data-target="#revisionModal"><i class="fa fa-history fa-fw"></i> Revision</a>
                </li>
                <li role="presentation"><a role="menuitem" class="ui-extra-slide" tabindex="-1" href="#" target="_blank" rel="noopener"><i class="fa fa-tv fa-fw"></i> Slide Mode</a>
                </li>
                
                <li class="divider"></li>
                <li class="dropdown-header">Import</li>
                <li role="presentation"><a role="menuitem" class="ui-import-dropbox" tabindex="-1" href="#" target="_self"><i class="fa fa-dropbox fa-fw"></i> Dropbox</a>
                </li>
                <li role="presentation"><a role="menuitem" class="ui-import-gist" href="#" data-toggle="modal" data-target="#gistImportModal"><i class="fa fa-github fa-fw"></i> Gist</a>
                </li>
                
                <li role="presentation"><a role="menuitem" class="ui-import-clipboard" href="#" data-toggle="modal" data-target="#clipboardModal"><i class="fa fa-clipboard fa-fw"></i> Clipboard</a>
                </li>
                <li class="divider"></li>
                <li class="dropdown-header">Download</li>
                <li role="presentation"><a role="menuitem" class="ui-download-markdown" tabindex="-1" href="#" target="_self"><i class="fa fa-file-text fa-fw"></i> Markdown</a>
                </li>
                <li role="presentation"><a role="menuitem" class="ui-download-html" tabindex="-1" href="#" target="_self"><i class="fa fa-file-code-o fa-fw"></i> HTML</a>
                </li>
                <li role="presentation"><a role="menuitem" class="ui-download-raw-html" tabindex="-1" href="#" target="_self"><i class="fa fa-file-code-o fa-fw"></i> Raw HTML</a>
                </li>
                <li class="divider"></li>
                <li role="presentation"><a role="menuitem" class="ui-help" href="#" data-toggle="modal" data-target=".help-modal"><i class="fa fa-question-circle fa-fw"></i> Help</a>
                </li>
            </ul>
            <div class="btn-group" data-toggle="buttons">
                <label class="btn ui-night" title="Night Theme">
                    <input type="checkbox" name="night"><i class="fa fa-moon-o"></i>
                </label>
            </div>
            <a class="btn btn-link ui-mode">
                <i class="fa fa-pencil"></i>
            </a>
        </div>
    </div>
    <div class="collapse navbar-collapse">
        <ul class="nav navbar-nav navbar-form navbar-left" style="padding:0;">
            <div class="btn-group" data-toggle="buttons">
                <label class="btn btn-default ui-view" for="view-mode-toggle-view" title="View (Ctrl+Alt+V)" aria-label="View (Ctrl+Alt+V)">
                    <input type="radio" name="mode" id="view-mode-toggle-view" autocomplete="off"><i class="fa fa-eye"></i>
                </label>
                <label class="btn btn-default ui-both" for="view-mode-toggle-both" title="Both (Ctrl+Alt+B)" aria-label="Both (Ctrl+Alt+B)">
                    <input type="radio" name="mode" id="view-mode-toggle-both" autocomplete="off"><i class="fa fa-columns"></i>
                </label>
                <label class="btn btn-default ui-edit" for="view-mode-toggle-edit" title="Edit (Ctrl+Alt+E)" aria-label="Edit (Ctrl+Alt+E)">
                    <input type="radio" name="mode" id="view-mode-toggle-edit" autocomplete="off"><i class="fa fa-pencil"></i>
                </label>
            </div>
            <div class="btn-group" data-toggle="buttons">
                <label class="btn ui-night" title="Night Theme">
                    <input type="checkbox" name="night"><i class="fa fa-moon-o"></i>
                </label>
            </div>
            <span class="btn btn-link btn-file ui-help" title="Help" data-toggle="modal" data-target=".help-modal">
                <i class="fa fa-question-circle"></i>
            </span>
        </ul>
        <ul class="nav navbar-nav navbar-right">
            <li id="online-user-list">
                <a class="ui-status" data-toggle="dropdown">
                    <span class="label label-danger"><i class="fa fa-plug"></i> OFFLINE</span>
                </a>
                <ul class="dropdown-menu list" role="menu" aria-labelledby="menu" style="right: 15px;width: 200px;">
                </ul>
            </li>
        </ul>
        <ul class="nav navbar-nav navbar-right" style="padding:0;">
            <li>
                <a href="https://poznamky.pernicka.cz/new" target="_blank" rel="noopener" class="ui-new">
                    <i class="fa fa-plus"></i> New
                </a>
            </li>
            <li>
                <a href="#" target="_blank" rel="noopener" class="ui-publish">
                    <i class="fa fa-share-square-o"></i> Publish
                </a>
            </li>
            <li>
                <a data-toggle="dropdown">
                    Menu <i class="fa fa-caret-down"></i>
                </a>
                <ul class="dropdown-menu list" role="menu" aria-labelledby="menu">
                    <li class="dropdown-header">Extra</li>
                    <li role="presentation"><a role="menuitem" class="ui-extra-revision" tabindex="-1" data-toggle="modal" data-target="#revisionModal"><i class="fa fa-history fa-fw"></i> Revision</a>
                    </li>
                    <li role="presentation"><a role="menuitem" class="ui-extra-slide" tabindex="-1" href="#" target="_blank" rel="noopener"><i class="fa fa-tv fa-fw"></i> Slide Mode</a>
                    </li>
                    
                    <li class="divider"></li>
                    <li class="dropdown-header">Import</li>
                    <li role="presentation"><a role="menuitem" class="ui-import-dropbox" tabindex="-1" href="#" target="_self"><i class="fa fa-dropbox fa-fw"></i> Dropbox</a>
                    </li>
                    <li role="presentation"><a role="menuitem" class="ui-import-gist" href="#" data-toggle="modal" data-target="#gistImportModal"><i class="fa fa-github fa-fw"></i> Gist</a>
                    </li>
                    
                    <li role="presentation"><a role="menuitem" class="ui-import-clipboard" href="#" data-toggle="modal" data-target="#clipboardModal"><i class="fa fa-clipboard fa-fw"></i> Clipboard</a>
                    </li>
                    <li class="divider"></li>
                    <li class="dropdown-header">Download</li>
                    <li role="presentation"><a role="menuitem" class="ui-download-markdown" tabindex="-1" href="#" target="_self"><i class="fa fa-file-text fa-fw"></i> Markdown</a>
                    </li>
                    <li role="presentation"><a role="menuitem" class="ui-download-html" tabindex="-1" href="#" target="_self"><i class="fa fa-file-code-o fa-fw"></i> HTML</a>
                    </li>
                    <li role="presentation"><a role="menuitem" class="ui-download-raw-html" tabindex="-1" href="#" target="_self"><i class="fa fa-file-code-o fa-fw"></i> Raw HTML</a>
                    </li>
                </ul>
            </li>
        </ul>
    </div>
</nav>
<div class="ui-spinner unselectable hidden-print"></div>

    <div class="row ui-content" style="display: none;">
    <div class="ui-edit-area unselectable">
        <textarea id="textit"></textarea>
    </div>
    <div class="ui-view-area">
        <div class="ui-infobar container-fluid unselectable hidden-print">
            <small>
                <span>
                    <span class="ui-lastchangeuser" style="display: none;">&thinsp;<i class="ui-user-icon small" data-toggle="tooltip" data-placement="right"></i></span>
                    <span class="ui-no-lastchangeuser">&thinsp;<i class="fa fa-clock-o fa-fw" style="width: 18px;"></i></span>&nbsp;
                    <span class="text-uppercase ui-status-lastchange changed">changed</span>
                    <span class="text-uppercase ui-status-lastchange created">created</span>
                    <span class="ui-lastchange text-uppercase"></span>
                </span>
                <span class="ui-permission dropdown pull-right">
                    <a id="permissionLabel" class="ui-permission-label text-uppercase" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">
                    </a>
                    <ul class="dropdown-menu" aria-labelledby="permissionLabel">
                        <li class="ui-permission-freely"><a><i class="fa fa-leaf fa-fw"></i> Freely - Anyone can edit</a></li>
                        <li class="ui-permission-editable"><a><i class="fa fa-shield fa-fw"></i> Editable - Signed-in people can edit</a></li>
                        <li class="ui-permission-limited"><a><i class="fa fa-id-card fa-fw"></i> Limited - Signed-in people can edit (forbid guests)</a></li>
                        <li class="ui-permission-locked"><a><i class="fa fa-lock fa-fw"></i> Locked - Only owner can edit</a></li>
                        <li class="ui-permission-protected"><a><i class="fa fa-umbrella fa-fw"></i> Protected - Only owner can edit (forbid guests)</a></li>
                        <li class="ui-permission-private"><a><i class="fa fa-hand-stop-o fa-fw"></i> Private - Only owner can view &amp; edit</a></li>
                        <li class="divider"></li>
                        <li class="ui-delete-note"><a><i class="fa fa-trash-o fa-fw"></i> Delete this note</a></li>
                    </ul>
                </span>
                <br>
                <span class="ui-owner" style="display: none;">
                    &thinsp;<i class="ui-user-icon small" data-toggle="tooltip" data-placement="right"></i>
                    &nbsp;<span class="text-uppercase">owned this note</span>
                </span>
            </small>
        </div>
        <div id="doc" class="markdown-body container-fluid"></div>
        <div class="ui-toc dropup unselectable hidden-print" style="display:none;">
            <div class="pull-right dropdown">
                <a id="tocLabel" class="ui-toc-label btn btn-default" data-toggle="dropdown" href="#" role="button" aria-haspopup="true" aria-expanded="false" title="Table of content">
                    <i class="fa fa-bars"></i>
                </a>
                <ul id="ui-toc" class="ui-toc-dropdown dropdown-menu" aria-labelledby="tocLabel">
                </ul>
            </div>
        </div>
        <div id="ui-toc-affix" class="ui-affix-toc ui-toc-dropdown unselectable hidden-print" data-spy="affix" style="top:51px;display:none;"></div>
    </div>
</div>
<!-- clipboard modal -->
<div class="modal fade" id="clipboardModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span>
                </button>
                <h4 class="modal-title" id="myModalLabel">Import from clipboard</h4>
            </div>
            <div class="modal-body">
                <div contenteditable data-ph="Paste your markdown or webpage here…" id="clipboardModalContent" style="overflow:auto;max-height:50vh"></div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" id="clipboardModalClear">Clear</button>
                <button type="button" class="btn btn-primary" id="clipboardModalConfirm">Import</button>
            </div>
        </div>
    </div>
</div>
<!-- locked modal -->
<div class="modal fade locked-modal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-sm">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span>
                </button>
                <h4 class="modal-title" id="myModalLabel"><i class="fa fa-lock"></i> This note is locked</h4>
            </div>
            <div class="modal-body" style="color:black;">
                <h5>Sorry, only the owner can edit this note.</h5>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-danger" data-dismiss="modal">OK</button>
            </div>
        </div>
    </div>
</div>
<!-- limit modal -->
<div class="modal fade limit-modal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-sm">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span>
                </button>
                <h4 class="modal-title" id="myModalLabel"><i class="fa fa-exclamation-triangle"></i> Reach the limit</h4>
            </div>
            <div class="modal-body" style="color:black;">
                <h5>Sorry, you&#39;ve reached the maximum length this note can be.</h5>
                <strong>Please shorten the note.</strong>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-warning" data-dismiss="modal">OK</button>
            </div>
        </div>
    </div>
</div>
<!-- message modal -->
<div class="modal fade message-modal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-sm">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span>
                </button>
                <h4 class="modal-title" id="myModalLabel"></h4>
            </div>
            <div class="modal-body" style="color:black;">
                <h5></h5>
                <a target="_blank" rel="noopener" style="word-break: break-all;"></a>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">OK</button>
            </div>
        </div>
    </div>
</div>
<!-- gist import modal -->
<div class="modal fade" id="gistImportModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span>
                </button>
                <h4 class="modal-title" id="myModalLabel">Import from Gist</h4>
            </div>
            <div class="modal-body">
                <input type="url" class="form-control" placeholder="Paste your gist url here… (like: https://gist.github.com/username/gistid)" id="gistImportModalContent">
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" id="gistImportModalClear">Clear</button>
                <button type="button" class="btn btn-primary" id="gistImportModalConfirm">Import</button>
            </div>
        </div>
    </div>
</div>
<!-- snippet import modal -->
<div class="modal fade" id="snippetImportModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span>
                </button>
                <h4 class="modal-title" id="myModalLabel">Import from Snippet</h4>
            </div>
            <div class="modal-body">
                <input type="hidden" id="snippetImportModalAccessToken" />
                <input type="hidden" id="snippetImportModalBaseURL" />
                <input type="hidden" id="snippetImportModalVersion" />
                <div class="ui-field-contain" style="display:table;margin-bottom:10px;width:100%;">
                    <div style="display:table-row;margin-bottom:5px;">
                        <label style="display:table-cell;">Project:</label>
                        <select class="form-control" id="snippetImportModalProjects" style="display:table-cell;" disabled="disabled">
                            <option value="init" selected="selected" disabled="disabled">Select From Available Projects</option>
                        </select>
                    </div>
                    <div style="display:table-row;">
                        <label style="display:table-cell;">Snippet</label>
                        <select class="form-control" id="snippetImportModalSnippets" style="display:table-cell;" disabled="disabled">
                            <option value="init" selected="selected" disabled="disabled">Select From Available Snippets</option>
                        </select>
                    </div>
                </div>
                <p class="snippet-import-or">OR</p>
                <input type="url" class="form-control" placeholder="/projects/:id/snippets/:snippet_id" id="snippetImportModalContent" disabled="disabled">
            </div>
            <div class="modal-footer">
                <span id="snippetImportModalLoading"><i class="fa fa-refresh fa-spin fa-fw"></i></span>
                <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" id="snippetImportModalClear">Clear</button>
                <button type="button" class="btn btn-primary" id="snippetImportModalConfirm" disabled="disabled">Import</button>
            </div>
        </div>
    </div>
</div>
<!-- snippet export modal -->
<div class="modal fade" id="snippetExportModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span>
                </button>
                <h4 class="modal-title" id="myModalLabel">Export to Snippet</h4>
            </div>
            <div class="modal-body">
                <input type="hidden" id="snippetExportModalAccessToken" />
                <input type="hidden" id="snippetExportModalBaseURL" />
                <input type="hidden" id="snippetExportModalVersion" />
                <div class="ui-field-contain" style="display:table;margin-bottom:10px;width:100%;">
                    <div style="display:table-row;margin-bottom:5px;">
                        <label style="display:table-cell;">Title:</label>
                        <input class="form-control" placeholder="new snippet" type="text" id="snippetExportModalTitle" />
                    </div>
                    <div style="display:table-row;margin-bottom:5px;">
                        <label style="display:table-cell;">File Name:</label>
                        <input class="form-control" placeholder="new_snippet.md" type="text" id="snippetExportModalFileName" />
                    </div>
                    <div style="display:table-row;margin-bottom:5px;">
                        <label style="display:table-cell;">Project:</label>
                        <select class="form-control" id="snippetExportModalProjects" style="display:table-cell;">
                            <option value="init" selected="selected" disabled="disabled">Select From Available Projects</option>
                        </select>
                    </div>
                    <div style="display:table-row;margin-bottom:5px;">
                        <label style="display:table-cell;">Visibility:</label>
                        <select class="form-control" id="snippetExportModalVisibility" style="display:table-cell;">
                            <option value="" selected="selected" disabled="disabled">Select Visibility Level</option>
                            <option value="0">Private</option>
                            <option value="10">Internal</option>
                        </select>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <span id="snippetExportModalLoading"><i class="fa fa-refresh fa-spin fa-fw"></i></span>
                <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" id="snippetExportModalConfirm">Export</button>
            </div>
        </div>
    </div>
</div>
<!-- delete modal -->
<div class="modal fade delete-modal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-sm">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span>
                </button>
                <h4 class="modal-title" id="myModalLabel">Are you sure?</h4>
            </div>
            <div class="modal-body">
                <h5 class="ui-delete-modal-msg">Do you really want to delete this note?</h5>
                <strong class="ui-delete-modal-item">All users will lose their connection.</strong>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger ui-delete-modal-confirm">Yes, do it!</button>
            </div>
        </div>
    </div>
</div>
<!-- refresh modal -->
<div class="modal fade" id="refreshModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-sm">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span>
                </button>
                <h4 class="modal-title" id="myModalLabel">This page needs to be refreshed</h4>
            </div>
            <div class="modal-body">
                <div class="incompatible-version">
                    <h5>Your client&#39;s version is incompatible.</h5>
                    <strong>Refresh to update.</strong>
                </div>
                <div class="new-version" style="display:none;">
                    <h5>New version available!</h5>
                    <a href="https://poznamky.pernicka.cz/s/release-notes" target="_blank" rel="noopener">See releases notes here</a>
                    <br>
                    <strong>Refresh to enjoy new features.</strong>
                </div>
                <div class="user-state-changed" style="display:none;">
                    <h5>Your user state has changed.</h5>
                    <strong>Refresh to load new user state.</strong>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-primary" id="refreshModalRefresh">Refresh</button>
            </div>
        </div>
    </div>
</div>

<!-- signin modal -->
<div class="modal fade signin-modal" tabindex="-1" role="dialog" aria-labelledby="mySmallModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-sm">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span>
                </button>
                <h4 class="modal-title" id="mySmallModalLabel">Choose method</h4>
            </div>
            <div class="modal-body" style="text-align: center;">
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                <h4>Sign in via E-Mail</h4>
                <form data-toggle="validator" role="form" class="form-horizontal" method="post" enctype="application/x-www-form-urlencoded">
                    <div class="form-group">
                        <div class="col-sm-12">
                            <input type="email" class="form-control" name="email" placeholder="E-Mail" required>
                            <span class="help-block control-label with-errors" style="display: inline;"></span>
                        </div>
                    </div>
                    <div class="form-group">
                        <div class="col-sm-12">
                            <input type="password" class="form-control" name="password" placeholder="Password" required>
                            <span class="help-block control-label with-errors" style="display: inline;"></span>
                        </div>
                    </div>
                    <div class="form-group">
                        <div class="col-sm-12">
                            <button type="submit" class="btn btn-primary" formaction="https://poznamky.pernicka.cz/login">Sign In</button>
                            
                        </div>
                    </div>
                </form>
                
            </div>
        </div>
    </div>
</div>

<!-- help modal -->
<div class="modal fade help-modal" tabindex="-1" role="dialog" aria-labelledby="mySmallModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span>
                </button>
                <h4 class="modal-title" id="mySmallModalLabel"><i class="fa fa-question-circle"></i> Help</h4>
            </div>
            <div class="modal-body">
                <div class="row">
                    <div class="col-lg-3">
                        <div class="panel panel-default">
                            <div class="panel-heading">
                                <h3 class="panel-title">Contacts</h3>
                            </div>
                            <div class="panel-body">
                                <a href="https://community.hedgedoc.org" target="_blank"><i class="fa fa-users fa-fw"></i> Join the community</a>
                                <br>
                                <a href="https://chat.hedgedoc.org" target="_blank"><i class="fa fa-hashtag fa-fw"></i> Meet us on Matrix</a>
                                <br>
                                <a href="https://github.com/hedgedoc/hedgedoc/issues" target="_blank"><i class="fa fa-tag fa-fw"></i> Report an issue</a>
                                <br>
                                <a href="https://translate.hedgedoc.org" target="_blank"><i class="fa fa-language fa-fw"></i> Help us translating</a>
                            </div>
                        </div>
                        <div class="panel panel-default">
                            <div class="panel-heading">
                                <h3 class="panel-title">Documents</h3>
                            </div>
                            <div class="panel-body">
                                <a href="./features" title="Features" target="_blank"><i class="fa fa-dot-circle-o fa-fw"></i> Features</a>
                                <br>
                                <a href="./yaml-metadata" title="YAML Metadata" target="_blank"><i class="fa fa-dot-circle-o fa-fw"></i> YAML Metadata</a>
                                <br>
                                <a href="./slide-example" title="Slide Example" target="_blank"><i class="fa fa-dot-circle-o fa-fw"></i> Slide Example</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-9">
                        <div class="panel panel-default">
                            <div class="panel-heading">
                                <h3 class="panel-title">Cheatsheet</h3>
                            </div>
                            <div class="panel-body" style="height: calc(100vh - 215px); overflow: auto;">
                                <table class="table table-condensed table-cheatsheet">
                                    <thead>
                                        <tr>
                                            <th>Example</th>
                                            <th>Syntax</th>
                                        </tr>
                                    </thead>
                                    <tbody class="markdown-body" style="font-family: inherit; font-size: 14px; padding: 0; max-width: inherit;">
                                        <tr>
                                            <td>Header</td>
                                            <td># Header</td>
                                        </tr>
                                        <tr>
                                            <td><ul><li>Unordered List</li></ul></td>
                                            <td>- Unordered List</td>
                                        </tr>
                                        <tr>
                                            <td><ol><li>Ordered List</li></ol></td>
                                            <td>1. Ordered List</td>
                                        </tr>
                                        <tr>
                                            <td><ul><li class="task-list-item"><input type="checkbox" class="task-list-item-checkbox" disabled><label></label>Checklist</li></ul></td>
                                            <td>- [ ] Checklist</td>
                                        </tr>
                                        <tr>
                                            <td><blockquote> Blockquote</blockquote></td>
                                            <td>> Blockquote</td>
                                        </tr>
                                        <tr>
                                            <td><strong>Bold</strong></td>
                                            <td>**Bold**</td>
                                        </tr>
                                        <tr>
                                            <td><i>Italicize</i></td>
                                            <td>*Italicize*</td>
                                        </tr>
                                        <tr>
                                            <td><s>Strikethrough</s></td>
                                            <td>~~Strikethrough~~</td>
                                        </tr>
                                        <tr>
                                            <td>19<sup>th</sup></td>
                                            <td>19^th^</td>
                                        </tr>
                                        <tr>
                                            <td>H<sub>2</sub>O</td>
                                            <td>H~2~O</td>
                                        </tr>
                                        <tr>
                                            <td><ins>Underlined text</ins></td>
                                            <td>++Underlined text++</td>
                                        </tr>
                                        <tr>
                                            <td><mark>Highlighted text</mark></td>
                                            <td>==Highlighted text==</td>
                                        </tr>
                                        <tr>
                                            <td><a>Link</a></td>
                                            <td>[link text](https:// "title")</td>
                                        </tr>
                                        <tr>
                                            <td>Image</td>
                                            <td>![image alt](https:// "title")</td>
                                        </tr>
                                        <tr>
                                            <td><code>Code</code></td>
                                            <td>`Code`</td>
                                        </tr>
                                        <tr>
                                            <td><pre style="border:none !important;"><code class="javascript hljs"><div class="wrapper"><div class="gutter linenumber"><span data-linenumber="1"></span></div><div class="code"><span class="hljs-keyword">var</span> i = <span class="hljs-number">0</span>;
</div></div></code></pre></td>
                                            <td>```javascript<br>var i = 0;<br>```</td>
                                        </tr>
                                        <tr>
                                            <td><img align="absmiddle" alt=":smile:" class="emoji" src="./build/emojify.js/dist/images/basic/smile.png" title=":smile:"></img></td>
                                            <td>:smile:</td>
                                        </tr>
                                        <tr>
                                            <td>Externals</td>
                                            <td>{%youtube youtube_id %}</td>
                                        </tr>
                                        <tr>
                                            <td>L<sup>a</sup>T<sub>e</sub>X</td>
                                            <td>$L^aT_eX$</td>
                                        </tr>
                                        <tr>
                                            <td><div class="alert alert-info"><p>This is an alert area.</p></div></td>
                                            <td>:::info<br>This is an alert area.<br>:::</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<style>
    table.table-cheatsheet tr > td:nth-child(2) {
        font-family: "Source Code Pro", Consolas, monaco, monospace;
        letter-spacing: 0.025em;
        line-height: 1.25;
    }
</style>

<!-- revision modal -->
<div class="modal fade" id="revisionModal" tabindex="-1" role="dialog" aria-labelledby="mySmallModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span>
                </button>
                <h4 class="modal-title" id="mySmallModalLabel"><i class="fa fa-history"></i> Revision</h4>
            </div>
            <div class="modal-body">
                <div class="row">
                    <div class="col-lg-4" style="max-height: calc(100vh - 215px); overflow: auto;">
                        <div class="list-group ui-revision-list"></div>
                    </div>
                    <div class="col-lg-8" style="height: calc(100vh - 215px); overflow: hidden;">
                        <textarea id="revisionViewer" style="display:none;"></textarea>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" id="revisionModalDownload">Download</button>
                <button type="button" class="btn btn-danger" id="revisionModalRevert">Revert</button>
            </div>
        </div>
    </div>
</div>

    <script src="https://poznamky.pernicka.cz/js/mathjax-config-extra.js"></script>
<script src="https://poznamky.pernicka.cz/build/MathJax/MathJax.js" defer></script>
<script src="https://poznamky.pernicka.cz/build/MathJax/config/TeX-AMS-MML_HTMLorMML.js" defer></script>
<script src="https://poznamky.pernicka.cz/build/MathJax/config/Safe.js" defer></script>
<script src="config"></script><script src="build/vendors~common.9f564b46f420cdda1117.js" defer="defer"></script><script src="build/common.04e0fea40de4509528e6.js" defer="defer"></script><script src="build/vendors~cover~cover-pack~index~index-pack~pretty~pretty-pack~slide~slide-pack.193d3c6702f23213ab74.js" defer="defer"></script><script src="build/vendors~index~index-pack~pretty~pretty-pack~slide~slide-pack.e57649d0b55ca32bef9f.js" defer="defer"></script><script src="build/index-pack.dd738613faa325361804.js" defer="defer"></script>

</body>

</html>
