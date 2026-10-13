// C# 앱이 점역 사이드카를 띄워 부르는 예. docs/sidecar.md 8절의 설정을 그대로 쓴다.
// CI(.github/workflows/windows.yml)가 windows-latest 에서 이 프로그램을 실제로 돌린다.
//
//   dotnet run --project examples/csharp-sidecar -- <python.exe 경로>
//
// 실패한 검사가 하나라도 있으면 종료 코드 1 이다.
using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

static class Program
{
    const string Sentence = "대한민국의 모든 국민은 법 앞에 평등하다.";
    // README '빠른 시작' 의 점자 앞에 문단 들여쓰기 두 칸(⠀⠀)이 붙는다(본문 요소, 32칸으로 안 접음).
    const string Expected = "⠀⠀⠊⠗⠚⠒⠑⠟⠈⠍⠁⠺⠀⠑⠥⠊⠵⠀⠈⠍⠁⠑⠟⠵⠀⠘⠎⠃⠀⠣⠲⠝⠀⠙⠻⠊⠪⠶⠚⠊⠲";

    static int failures;

    static void Check(bool ok, string what, string detail = "")
    {
        Console.WriteLine($"{(ok ? "PASS" : "FAIL")}  {what}" + (detail.Length > 0 ? $"   [{detail}]" : ""));
        if (!ok) failures++;
    }

    static Process Start(string python, Encoding stdinEncoding)
    {
        var psi = new ProcessStartInfo
        {
            FileName = python,
            Arguments = "-m semojum_braille.sidecar",
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,              // 7절: 표준오류는 비동기로 읽어 비운다(안 비우면 파이프가 차서 멈춘다)
            UseShellExecute = false,
            CreateNoWindow = true,
            StandardInputEncoding = stdinEncoding,     // 8절: 이 둘이 핵심이다. 안 주면 콘솔 코드 페이지(한국어 윈도우는 cp949)를 쓴다
            StandardOutputEncoding = new UTF8Encoding(false),
            // 작업 폴더에 다른 semojum_braille 폴더가 있으면 `-m` 이 깔린 패키지 대신 그것을 먼저 올린다. 빈 폴더에서 띄운다.
            WorkingDirectory = Path.GetTempPath(),
        };
        psi.Environment["PYTHONUTF8"] = "1";
        var p = new Process { StartInfo = psi };
        p.ErrorDataReceived += (_, e) => { if (e.Data != null) Console.WriteLine("  [사이드카 stderr] " + e.Data); };
        p.Start();
        p.BeginErrorReadLine();
        return p;
    }

    static void Send(Process p, string line)
    {
        p.StandardInput.WriteLine(line);   // 줄 끝은 윈도우 기본 \r\n. 사이드카는 \n 과 \r\n 을 다 받는다
        p.StandardInput.Flush();
    }

    // 응답 한 줄. 요청과 응답은 줄 수가 아니라 id 로 짝짓는다(빈 줄에는 응답이 없다).
    static JsonObject Read(Process p, int timeoutMs = 120_000)
    {
        Task<string?> t = p.StandardOutput.ReadLineAsync();
        if (!t.Wait(timeoutMs)) throw new TimeoutException($"{timeoutMs} ms 안에 응답이 없다");
        string line = t.Result ?? throw new IOException("사이드카가 표준출력을 닫았다(죽음)");
        return JsonNode.Parse(line)!.AsObject();
    }

    static int Id(JsonObject r) => r["id"]?.GetValue<int>() ?? -1;

    static int Main(string[] args)
    {
        try { Console.OutputEncoding = new UTF8Encoding(false); } catch (IOException) { }   // CI 로그에서 한글이 ? 로 안 깨지게. 콘솔이 없으면 넘어간다
        string python = args.Length > 0 ? args[0] : "python";
        var asciiJson = new JsonSerializerOptions();                                                       // 기본: 한글 · 점자를 \uXXXX 로(ASCII)
        var utf8Json = new JsonSerializerOptions { Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping };  // 한글을 그대로
        object Translate(int id) => new { id, op = "translate", text = Sentence, type = "text", heading_level = 0 };

        Console.WriteLine($"== 권장 설정: 표준입력 · 표준출력 UTF-8(BOM 없음) · PYTHONUTF8=1 · python {python}");
        var clock = Stopwatch.StartNew();
        using (Process p = Start(python, new UTF8Encoding(false)))
        {
            Send(p, JsonSerializer.Serialize(new { id = 1, op = "ping" }));
            JsonObject r = Read(p);
            Check(Id(r) == 1 && r["protocol"]?.GetValue<int>() == 1, "ping 이 protocol 1 을 알린다",
                  $"version {r["version"]} · 기동부터 첫 응답 {clock.ElapsedMilliseconds} ms");

            string line = JsonSerializer.Serialize(Translate(2), asciiJson);
            Check(line.IndexOf('대') < 0, "System.Text.Json 기본 직렬화는 ASCII 다(한글이 \\uXXXX)");
            clock.Restart();
            Send(p, line);
            r = Read(p);
            string cells = r["cells"]?.GetValue<string>() ?? "";
            Check(Id(r) == 2 && cells == Expected, "translate(ASCII 로 보냄): README 와 같은 점자",
                  $"{cells.Length}칸 · {clock.ElapsedMilliseconds} ms");
            JsonArray breaks = r["breaks"]?.AsArray() ?? new JsonArray();
            bool sorted = true;
            for (int i = 0; i < breaks.Count; i++)
            {
                int b = breaks[i]!.GetValue<int>();
                sorted &= b > 0 && b < cells.Length && (i == 0 || breaks[i - 1]!.GetValue<int>() < b);
            }
            Check(breaks.Count > 0 && sorted, "breaks 는 cells 안의 오름차순 인덱스다(C# string 인덱스 그대로)", $"{breaks.Count}개");

            Send(p, JsonSerializer.Serialize(Translate(3), utf8Json));
            r = Read(p);
            Check(Id(r) == 3 && r["cells"]?.GetValue<string>() == Expected, "translate(한글을 UTF-8 그대로 보냄): 같은 점자");

            Send(p, JsonSerializer.Serialize(new { id = 4, op = "decode", braille = "⠊⠗⠚⠒⠑⠟⠈⠍⠁" }));
            r = Read(p);
            Check(Id(r) == 4 && r["text"]?.GetValue<string>() == "대한민국", "decode 가 묵자로 되돌린다", $"{r["text"]}");

            Send(p, "");                                                           // 빈 줄에는 응답이 없다
            Send(p, JsonSerializer.Serialize(new { id = 5, op = "ping" }));
            r = Read(p);
            Check(Id(r) == 5, "빈 줄 다음 요청의 응답이 바로 온다(줄 수가 아니라 id 로 짝짓는다)");

            p.StandardInput.Close();                                               // 표준입력을 닫으면 사이드카가 끝난다
            Check(p.WaitForExit(30_000) && p.ExitCode == 0, "표준입력을 닫으면 종료 코드 0 으로 끝난다");
        }

        Console.WriteLine("== 잘못된 설정: 표준입력을 cp949(한국어 윈도우 콘솔 기본)로 둔다");
        Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);
        using (Process p = Start(python, Encoding.GetEncoding(949)))
        {
            Send(p, JsonSerializer.Serialize(Translate(6), utf8Json));
            JsonObject r = Read(p);
            Check(Id(r) == 6 && r["error"] != null && r["cells"] == null,
                  "한글을 cp949 바이트로 보내면 깨진 점자가 아니라 error 가 온다(id 는 돌려준다)", $"{r["error"]}");

            Send(p, JsonSerializer.Serialize(Translate(7), asciiJson));
            r = Read(p);
            Check(Id(r) == 7 && r["cells"]?.GetValue<string>() == Expected,
                  "같은 설정이라도 ASCII 로 보내면 맞다(2절이 ASCII 를 권하는 까닭)");
            p.StandardInput.Close();
            p.WaitForExit(30_000);
        }

        Console.WriteLine(failures == 0 ? "전부 통과" : $"실패 {failures}건");
        return failures == 0 ? 0 : 1;
    }
}
